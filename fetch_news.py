#!/usr/bin/env python3
"""
AI全球资讯 - 每日内容自动抓取脚本
抓取 RSS / API -> 生成 js/data.js

数据源：
  - TechCrunch AI (RSS)
  - The Verge AI (RSS)
  - VentureBeat AI (RSS)
  - 36氪 AI频道 (RSS)
  - 量子位 (RSS)
  - arXiv cs.AI/cs.CL/cs.CV (API)
  - GitHub Trending (via GitHub Search API)
"""

import sys
import json
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
import os
import time
import ssl

# 禁用 SSL 证书验证（部分网络环境下需要）
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# ============================================================
# 翻译模块（英文 -> 中文）
# ============================================================
_translator = None
_translate_cache = {}

def _get_translator():
    """延迟加载翻译器（避免启动时网络阻塞）"""
    global _translator
    if _translator is None:
        try:
            from deep_translator import GoogleTranslator
            _translator = GoogleTranslator(source='en', target='zh-CN')
            print('  [OK] 翻译模块加载成功（GoogleTranslator）')
        except Exception as e:
            print(f'  [WARN] 翻译模块加载失败: {e}')
            _translator = False
    return _translator

def translate_to_zh(text):
    """将英文翻译为中文，失败则返回原文"""
    if not text or not isinstance(text, str):
        return text
    text = text.strip()
    if not text:
        return text
    # 如果主要是中文，跳过翻译
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    if chinese_chars > len(text) * 0.3:
        return text
    if text in _translate_cache:
        return _translate_cache[text]
    try:
        t = _get_translator()
        if not t:
            return text
        result = t.translate(text[:500])  # 限制长度，加速翻译
        if result:
            _translate_cache[text] = result
        return result or text
    except Exception as e:
        print(f'  [WARN] 翻译失败: {str(e)[:60]}')
        _translate_cache[text] = text  # 缓存失败结果，避免重复尝试
        return text

# ============================================================
# 配置区
# ============================================================
RSS_SOURCES = [
    ('TechCrunch AI',    'https://techcrunch.com/feed/',              'en', 'llm'),
    ('The Verge AI',     'https://www.theverge.com/rss/artificial-intelligence/index.xml', 'en', 'industry'),
    ('VentureBeat AI',   'https://venturebeat.com/category/ai/feed/', 'en', 'industry'),
    ('36氪 AI',          'https://36kr.com/feed',                              'zh', 'industry'),
    ('量子位',           'https://www.qbitai.com/rss',                     'zh', 'llm'),
    ('MIT Tech Review',  'https://www.technologyreview.com/feed/',        'en', 'research'),
]

ARXIV_CATEGORIES = ['cs.AI', 'cs.CL', 'cs.CV']
ARXIV_MAX_RESULTS = 15

GITHUB_SEARCH_URL = (
    'https://api.github.com/search/repositories'
    '?q=stars:>500+pushed:>{date}'
    '&sort=stars&order=desc&per_page=15'
)

# 输出文件路径（相对于脚本所在目录）
OUTPUT_JS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'js', 'data.js')

# BG 渐变色池（自动分配）
BG_POOL = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
    'linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)',
    'linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)',
    'linear-gradient(135deg, #f5576c 0%, #ff6a88 100%)',
    'linear-gradient(135deg, #667eea 0%, #43e97b 100%)',
]

TAG_CLASS_POOL = ['tag-purple', 'tag-orange', 'tag-blue', 'tag-red', 'tag-green']
LANG_CLASS_MAP = {
    'Python': 'lang-python', 'JavaScript': 'lang-javascript', 'TypeScript': 'lang-typescript',
    'Go': 'lang-go', 'Rust': 'lang-rust', 'C++': 'lang-cpp',
    'Jupyter Notebook': 'lang-python', 'Shell': 'lang-bash',
}
# ============================================================


def http_get(url, timeout=15, headers=None):
    """简单的 HTTP GET，返回 (status_code, text)"""
    try:
        req = urllib.request.Request(url, headers=headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/xml, application/json, text/html, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            charset = 'utf-8'
            ct = resp.headers.get('Content-Type', '')
            m = re.search(r'charset=([\w-]+)', ct)
            if m:
                charset = m.group(1)
            return resp.status, resp.read().decode(charset, errors='replace')
    except Exception as e:
        print(f'  [WARN] GET {url[:60]}... 失败: {e}')
        return None, None


def parse_rss(url, source_name, lang, category):
    """解析 RSS/Atom，返回标准化文章列表"""
    print(f'  · 抓取 RSS: {source_name} ({url[:60]}...)')
    status, content = http_get(url)
    if not content:
        return []
    items = []
    try:
        root = ET.fromstring(content)
        entries = (root.findall('.//item') or
                   root.findall('.//{http://purl.org/rss/1.0/}item') or
                   root.findall('.//{http://www.w3.org/2005/Atom}entry'))
        if not entries:
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('.//atom:entry', ns)

        for entry in entries[:10]:
            title = _get_xml_text(entry, ['title', '{http://www.w3.org/2005/Atom}title'])
            link  = _get_xml_text(entry, ['link', '{http://www.w3.org/2005/Atom}link'])
            if link and link.startswith('<'):
                link_elem = entry.find('{http://www.w3.org/2005/Atom}link')
                if link_elem is not None:
                    link = link_elem.get('href', '')
            summary = _get_xml_text(entry, [
                'description', 'summary', '{http://www.w3.org/2005/Atom}summary',
                '{http://www.w3.org/2005/Atom}content'
            ])
            pub_date = _get_xml_text(entry, [
                'pubDate', 'published', '{http://www.w3.org/2005/Atom}published',
                'updated', '{http://www.w3.org/2005/Atom}updated'
            ])
            clean_title   = _clean_html(title) if title else ''
            clean_summary = _clean_html(summary) if summary else ''
            items.append({
                'title': translate_to_zh(clean_title)[:120],
                'link': link,
                'summary': translate_to_zh(clean_summary)[:200],
                'pub_date': _normalize_time(pub_date),
                'source': source_name,
                'lang': lang,
                'category': category,
            })
    except Exception as e:
        print(f'  [WARN] 解析 RSS {source_name} 失败: {e}')
    return items


def _get_xml_text(element, tag_names):
    for tag in tag_names:
        e = element.find(tag)
        if e is not None and e.text:
            return e.text.strip()
        if tag.endswith('link}'):
            e = element.find(tag)
            if e is not None:
                return e.get('href', '')
    return ''


def fetch_arxiv(categories, max_results=10):
    """从 arXiv API 获取最新论文"""
    print(f'  · 抓取 arXiv: {", ".join(categories)}')
    cat_query = '+OR+'.join(f'cat:{c}' for c in categories)
    url = (
        f'http://export.arxiv.org/api/query?'
        f'search_query={cat_query}'
        f'&sortBy=submittedDate&sortOrder=descending'
        f'&max_results={max_results}'
    )
    status, content = http_get(url, timeout=20)
    if not content:
        return []
    items = []
    try:
        root = ET.fromstring(content)
        ns = {'atom': 'http://www.w3.org/2005/Atom',
               'arxiv': 'http://arxiv.org/schemas/atom'}
        for entry in root.findall('atom:entry', ns):
            title_elem = entry.find('atom:title', ns)
            raw_title = ''
            if title_elem is not None:
                raw_title = (title_elem.text or '').strip()
            raw_title = re.sub(r'\s+', ' ', raw_title).strip()

            summary_elem = entry.find('atom:summary', ns)
            raw_summary = ''
            if summary_elem is not None:
                raw_summary = (summary_elem.text or '').strip()
            raw_summary = re.sub(r'\s+', ' ', raw_summary).strip()

            if not raw_title:
                link_elem = entry.find('atom:id', ns)
                link_txt = (link_elem.text or '')[:60] if link_elem is not None else 'unknown'
                print(f'  [WARN] 跳过无标题论文: {link_txt}')
                continue

            published_elem = entry.find('atom:published', ns)
            link_elem = entry.find('atom:id', ns)

            authors = []
            for a in entry.findall('atom:author', ns)[:3]:
                name_elem = a.find('atom:name', ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            cat_elems = entry.findall('atom:category', ns)
            cats = [c.get('term', '') for c in cat_elems]

            items.append({
                'title': translate_to_zh(raw_title)[:120],
                'link': (link_elem.text or '') if link_elem is not None else '',
                'summary': translate_to_zh(raw_summary)[:200],
                'pub_date': _normalize_time((published_elem.text or '') if published_elem is not None else ''),
                'source': 'arXiv',
                'authors': ', '.join(authors),
                'categories': cats,
                'lang': 'en',
                'category': 'paper',
            })
    except Exception as e:
        print(f'  [WARN] 解析 arXiv 失败: {e}')
    return items


def fetch_github_trending():
    """使用 GitHub Search API 获取近期热门仓库"""
    print('  · 抓取 GitHub Trending...')
    items = []
    try:
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        url = GITHUB_SEARCH_URL.format(date=yesterday)
        status, content = http_get(url, timeout=15, headers={
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AI-News-Fetcher/1.0',
        })
        if status == 200 and content:
            data = json.loads(content)
            for repo in data.get('items', [])[:15]:
                lang = repo.get('language', '') or 'Unknown'
                raw_desc = repo.get('description', '') or ''
                items.append({
                    'rank': 0,
                    'name': repo['full_name'],
                    'desc': translate_to_zh(raw_desc),
                    'lang': lang,
                    'langClass': LANG_CLASS_MAP.get(lang, 'lang-python'),
                    'stars': f"+{repo['stargazers_count']:,}",
                    'url': repo['html_url'],
                })
        else:
            print(f'  [WARN] GitHub Search API 返回 status={status}，使用备用方案')
            status2, html = http_get('https://github.com/trending?since=daily', timeout=15)
            if html:
                names = re.findall(r'<h2[^>]*>.*?href="/([^"]+)"', html, re.DOTALL)
                descs = re.findall(r'<p[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL)
                langs = re.findall(r'<span[^>]*itemprop="programmingLanguage"[^>]*>(.*?)</span>', html)
                for i, name in enumerate(names[:15]):
                    lang = langs[i].strip() if i < len(langs) else ''
                    raw_desc = _clean_html(descs[i]) if i < len(descs) else ''
                    items.append({
                        'rank': 0,
                        'name': name.strip(),
                        'desc': translate_to_zh(raw_desc),
                        'lang': lang,
                        'langClass': LANG_CLASS_MAP.get(lang, 'lang-python'),
                        'stars': '',
                        'url': f'https://github.com/{name.strip()}',
                    })
    except Exception as e:
        print(f'  [WARN] GitHub Trending 抓取失败: {e}')
    return items


def _clean_html(text):
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    return text.strip()


def _normalize_time(pub_date_str):
    """将各种日期格式转为 'X小时前' / 'X天前' / 'YYYY-MM-DD'"""
    if not pub_date_str:
        return '今天'
    try:
        import email.utils
        try:
            dt = email.utils.parsedate_to_datetime(pub_date_str.strip())
            return _format_time_diff(dt)
        except Exception:
            pass
        for fmt in ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S']:
            try:
                dt = datetime.datetime.strptime(pub_date_str.strip()[:25], fmt)
                return _format_time_diff(dt)
            except ValueError:
                continue
        m = re.search(r'(\d{4}-\d{2}-\d{2})', pub_date_str)
        if m:
            return m.group(1)
        return pub_date_str[:16]
    except Exception:
        return pub_date_str[:16] if pub_date_str else '今天'

def _format_time_diff(dt):
    """计算与当前的时间差，返回中文描述"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - dt
    if diff.days == 0:
        hours = int(diff.seconds / 3600)
        return f'{hours}小时前' if hours > 0 else '刚刚'
    elif diff.days == 1:
        return '昨天'
    elif diff.days < 7:
        return f'{diff.days}天前'
    else:
        return dt.strftime('%Y-%m-%d')


def classify_category(title, summary, category_hint):
    """根据标题和摘要细化分类"""
    text = (title + ' ' + summary).lower()
    if any(k in text for k in ['gpt', 'llama', 'gemini', 'claude', 'qwen', 'chatgpt', '大模型', 'llm']):
        return 'llm'
    if any(k in text for k in ['ai agent', 'application', 'tool', 'product', '应用', '发布', 'launch']):
        return 'application'
    if any(k in text for k in ['arxiv', 'paper', 'research', 'studies', '论文', '研究', 'benchmark']):
        return 'research'
    if any(k in text for k in ['funding', 'invest', 'ipo', '融资', '投资', '政策', '法案', 'act', 'policy']):
        return 'industry' if '政策' not in text and 'act' not in text else 'policy'
    return category_hint or 'industry'


def assign_bg(index):
    return BG_POOL[index % len(BG_POOL)]


def build_carousel_slides(articles):
    """取最新 4 条作为轮播图"""
    slides = []
    tag_map = {
        'llm': '头条 · 大模型',
        'research': '独家 · 研究',
        'application': '重磅 · 应用',
        'industry': '行业 · 动态',
        'policy': '政策 · 法规',
    }
    for i, a in enumerate(articles[:4]):
        cat = a.get('category', 'industry')
        slides.append({
            'tag': tag_map.get(cat, '头条 · 突破'),
            'title': a['title'][:80],
            'summary': a.get('summary', '')[:100] or a['title'][:100],
            'source': a.get('source', 'AI资讯'),
            'time': a.get('pub_date', '今天'),
            'views': f"{max(10, 100 - i*15)}.{i*3}K",
            'bg': assign_bg(i),
            'url': a.get('link', ''),
        })
    while len(slides) < 4:
        slides.append({
            'tag': '头条 · 资讯',
            'title': 'AI全球资讯持续更新中，敬请期待更多精彩内容',
            'summary': '我们每日自动抓取全球最新 AI 资讯，为您带来最前沿的科技动态',
            'source': 'AI全球资讯',
            'time': datetime.datetime.now().strftime('%Y-%m-%d'),
            'views': '10.0K',
            'bg': assign_bg(len(slides)),
        })
    return slides


def build_quick_news(articles):
    """生成快讯列表（最新 8 条）"""
    quick = []
    for a in articles[:8]:
        quick.append({
            'time': datetime.datetime.now().strftime('%H:%M'),
            'text': a['title'][:60],
            'hot': len(quick) == 0,
            'url': a.get('link', ''),
        })
    while len(quick) < 8:
        quick.append({'time': '--:--', 'text': '资讯持续更新中...', 'hot': False})
    return quick


def build_llm_section(articles):
    """大模型动态板块"""
    items = []
    llm_articles = [a for a in articles if a.get('category') in ('llm', 'industry')][:5]
    cat_key_map = {'llm': 'gpt', 'industry': 'domestic'}

    for i, a in enumerate(llm_articles):
        cat = a.get('category', 'llm')
        item = {
            'title': a['title'][:80],
            'source': a.get('source', ''),
            'time': a.get('pub_date', '今天'),
            'views': f"{max(5, 80 - i*10)}.{i*7}K",
            'comments': str(max(10, 300 - i*40)),
            'bg': assign_bg(i + 4),
            'category': cat_key_map.get(cat, 'gpt'),
            'url': a.get('link', ''),
        }
        if i == 0:
            item['featured'] = True
            item['tag'] = '重磅'
            item['desc'] = a.get('summary', a['title'])[:120] + '...'
        items.append(item)

    return {
        'title': '大模型动态',
        'icon': '🧠',
        'tabs': [
            {'key': 'all', 'label': '全部'},
            {'key': 'gpt', 'label': 'GPT'},
            {'key': 'claude', 'label': 'Claude'},
            {'key': 'gemini', 'label': 'Gemini'},
            {'key': 'domestic', 'label': '国产'},
        ],
        'items': items,
    }


def build_research_section(arxiv_articles, rss_articles):
    """AI研究板块（来自 arXiv + RSS 研究类）"""
    items = []
    research_articles = []
    research_articles.extend(arxiv_articles[:6])
    research_articles.extend([a for a in rss_articles if a.get('category') == 'research'][:4])

    tag_map = {0: ('论文解读', 'tag-purple'), 1: ('学术会议', 'tag-orange'),
               2: ('技术报告', 'tag-blue'), 3: ('基准测试', 'tag-red')}

    for i, a in enumerate(research_articles[:6]):
        tag, tag_cls = tag_map.get(i % 4, ('论文', 'tag-purple'))
        items.append({
            'title': ('【arXiv】' if a.get('source') == 'arXiv' else '') + a['title'][:90],
            'desc': a.get('summary', '')[:150] + '...' if a.get('summary') else a['title'][:150] + '...',
            'tag': tag,
            'tagClass': tag_cls,
            'source': a.get('source', 'arXiv'),
            'time': a.get('pub_date', '今天'),
            'bg': assign_bg(i + 6),
            'category': 'paper',
            'url': a.get('link', ''),
        })

    return {
        'title': 'AI研究',
        'icon': '🔬',
        'tabs': [
            {'key': 'paper', 'label': '论文'},
            {'key': 'benchmark', 'label': '基准测试'},
            {'key': 'theory', 'label': '理论突破'},
        ],
        'layout': 'list',
        'items': items,
    }


def build_application_section(articles):
    """AI应用板块（排行榜形式）"""
    items = []
    app_articles = [a for a in articles if a.get('category') == 'application'][:10]
    emojis = ['🔥', '💡', '🎬', '🔍', '⚖️', '🎵', '📝', '🤖', '📊', '🌐']

    for i, a in enumerate(app_articles[:10]):
        items.append({
            'rank': i + 1,
            'title': a['title'][:70],
            'time': a.get('pub_date', '今天'),
            'emoji': emojis[i % len(emojis)],
            'url': a.get('link', ''),
        })
    while len(items) < 6:
        items.append({'rank': len(items)+1, 'title': 'AI应用资讯持续更新中...', 'time': '今天'})
    return {
        'title': 'AI应用',
        'icon': '⚡',
        'items': items,
    }


def build_industry_section(articles):
    """行业动态板块"""
    items = []
    ind_articles = [a for a in articles if a.get('category') == 'industry'][:10]
    emojis = ['🔥', '💰', '🏭', '🌏', '📉', '🔄', '🚀', '🤝', '📰', '🏢']

    for i, a in enumerate(ind_articles[:10]):
        items.append({
            'rank': i + 1,
            'title': a['title'][:70],
            'time': a.get('pub_date', '今天'),
            'emoji': emojis[i % len(emojis)],
            'url': a.get('link', ''),
        })

    return {
        'title': '行业动态',
        'icon': '📊',
        'items': items,
    }


def build_policy_section():
    """政策法规（保留静态，此类内容需要人工审核）"""
    return {
        'title': '政策法规',
        'icon': '⚖️',
        'items': [
            {
                'flag': '🇪🇺',
                'title': '欧盟《AI法案》全面生效：全球最严AI监管落地实施',
                'desc': '高风险AI系统需经过严格合规审查，违规企业最高面临全球营业额6%的罚款。首批受影响企业名单已公布。',
                'date': '2026-05-01 生效',
                'level': '强制性',
                'url': 'https://artificialintelligenceact.eu/'
            },
            {
                'flag': '🇨🇳',
                'title': '中国发布《生成式AI服务管理暂行办法》修订版',
                'desc': '新增关于AI训练数据版权保护条款，要求服务提供者建立内容溯源机制，强化深度合成标识规范。',
                'date': '2026-04-15 发布',
                'level': '部门规章',
                'url': 'https://www.cac.gov.cn/2023-07/13/c_1690898327011755.htm'
            },
            {
                'flag': '🇺🇸',
                'title': '美国白宫发布《AI权利法案蓝图》2.0版本',
                'desc': '强调算法透明度、隐私保护和反歧视原则，要求联邦政府所有AI采购必须通过伦理审查流程。',
                'date': '2026-03-20 更新',
                'level': '行政指导',
                'url': 'https://www.whitehouse.gov/ostp/ai-bill-of-rights/'
            }
        ]
    }


def build_open_source_section(github_repos):
    """开源项目热榜"""
    projects = []
    for i, repo in enumerate(github_repos[:8]):
        repo['rank'] = i + 1
        if 'stars' not in repo or not repo['stars']:
            repo['stars'] = f"+{max(100, 2000 - i*200)}"
        if 'langClass' not in repo:
            repo['langClass'] = LANG_CLASS_MAP.get(repo.get('lang', ''), 'lang-python')
        projects.append(repo)

    while len(projects) < 6:
        projects.append({
            'rank': len(projects) + 1,
            'name': 'awaiting/new-project',
            'desc': '项目数据持续采集中...',
            'lang': 'Python',
            'langClass': 'lang-python',
            'stars': '+0',
        })

    return {
        'title': '开源项目热榜',
        'icon': '🔓',
        'moreLink': 'https://github.com/trending?since=daily',
        'moreText': 'GitHub Trending →',
        'projects': projects,
    }


def build_sidebar_hot_rank(articles):
    """侧栏热榜 TOP10"""
    hot = []
    for i, a in enumerate(articles[:10]):
        hot.append({
            'rank': i + 1,
            'top3': i < 3,
            'title': a['title'][:50],
            'heat': f"{max(10, 120 - i*10)}.{i*3}万热度" if i < 3 else '',
            'url': a.get('link', ''),
        })
    while len(hot) < 10:
        hot.append({'rank': len(hot)+1, 'top3': False, 'title': '持续更新中...'})
    return hot


def build_tags_cloud(articles):
    """从文章标题中提取关键词生成标签云（使用结巴分词）"""
    import collections, re

    # 尝试加载结巴分词
    _jieba = None
    try:
        import jieba
        jieba.initialize()
        _jieba = jieba
        print('  [OK] 结巴分词加载成功')
    except Exception as e:
        print(f'  [WARN] 结巴分词加载失败，使用正则模式: {e}')

    stop_words = {
        # 英文停用词
        'the', 'a', 'an', 'and', 'or', 'of', 'to', 'in', 'for', 'on', 'is', 'it',
        'that', 'this', 'with', 'from', 'by', 'as', 'are', 'was', 'be', 'has',
        'will', 'can', 'new', 'how', 'what', 'why', 'when', 'where',
        'ai', 'the', 'we', 'our', 'you', 'they', 'he', 'she',
        'have', 'has', 'had', 'been', 'being', 'do', 'does', 'did',
        'but', 'not', 'so', 'if', 'on', 'at', 'by', 'for', 'with', 'about',
        # 中文停用词（高频无意义词）
        '的', '了', '在', '是', '和', '与', '中', '为', '吗', '呢', '吧', '啊',
        '也', '都', '很', '还', '就', '又', '让', '被', '把', '对', '这', '那',
        '我们', '一个', '通过', '这是', '提供', '进行', '工作', '领域',
        '可以', '已经', '这个', '那个', '没有', '不是', '只是', '这样',
        '如何', '为什么', '什么', '哪个', '哪里', '怎么', '吗', '呢',
        '能', '会', '要', '去', '来', '做', '用', '想', '知道', '看到',
        'Non', 'None', 'True', 'False',
        '说', '看', '好', '多', '少', '大', '小', '上', '下', '里', '外',
        '使用', '利用', '基于', '支持', '包括', '需要', '用于', '采用',
        '目前', '近日', '今天', '昨天', '正式', '成功', '介绍', '表示',
        '推出', '发布', '获得', '实现', '提升', '完善', '优化', '增强',
        '以及', '或者', '同时', '虽然', '因为', '所以', '而且', '并且',
        # 泛化无意义词（需持续补充）
        '正在', '系统', '技术', '数据', '公司', '工作', '领域', '一种',
        '世界', '问题', '提供', '进行', '能力', '方式', '方法', '情况',
        '结果', '过程', '时间', '地点', '原因', '目的', '对象', '内容',
        '部分', '全部', '很多', '一些', '这个', '那个', '什么', '怎样',
    }

    word_counter = collections.Counter()

    for a in articles:
        text = a.get('title', '') + ' ' + a.get('summary', '')

        # 英文技术术语（完整提取）
        for word in re.findall(r'\b[A-Z][A-Za-z0-9]{1,20}\b', text):
            wl = word.lower()
            if wl not in stop_words:
                word_counter[word] += 2

        if _jieba:
            import jieba.posseg as pseg
            for word, flag in pseg.lcut(text):
                word = word.strip()
                if len(word) >= 2 and word not in stop_words:
                    # 只保留名词(n)、专有名词(nr/ns/nt/nz)、英文词(eng)、未知词(x，常是术语)
                    if flag.startswith('n') or flag in ('eng', 'x', 't'):
                        word_counter[word] += 1
        else:
            for word in re.findall(r'[\u4e00-\u9fff]{2,6}', text):
                if word not in stop_words:
                    word_counter[word] += 1

    # 只保留出现≥2次的有意义关键词
    top_tags = [w for w, cnt in word_counter.most_common(30) if cnt >= 2][:15]

    size_map = ['large', 'large', 'medium', 'medium', 'medium',
                'small', 'small', 'small', 'small', 'small',
                'small', 'small', 'small', 'small', 'small']

    tags = []
    for i, tag in enumerate(top_tags):
        tags.append({'text': tag, 'size': size_map[i] if i < len(size_map) else 'small'})
    return tags


def build_search_data(articles, quick_news):
    """搜索索引数据"""
    search_data = []
    seen = set()
    all_items = articles + [{'title': q['text'], 'category': 'news', 'tag': '', 'summary': q['text']} for q in quick_news]
    for item in all_items:
        title = item.get('title', '')
        if not title or title in seen:
            continue
        seen.add(title)
        cat = item.get('category', 'news')
        cat_label_map = {
            'llm': '大模型动态', 'research': 'AI研究', 'application': 'AI应用',
            'industry': '行业动态', 'policy': '政策法规', 'news': '快讯'
        }
        search_data.append({
            'title': title[:100],
            'category': cat_label_map.get(cat, 'AI资讯'),
            'tag': item.get('tag', cat),
            'snippet': item.get('summary', title)[:120],
        })
    return search_data[:30]


def main():
    print('=' * 60)
    print(f'AI全球资讯 - 每日内容抓取 {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 60)

    # 1. 抓取 RSS
    print('\n[1/5] 抓取 RSS 源...')
    rss_articles = []
    for source_name, url, lang, cat in RSS_SOURCES:
        items = parse_rss(url, source_name, lang, cat)
        rss_articles.extend(items)
        time.sleep(0.5)
    print(f'  [OK] RSS 共抓取 {len(rss_articles)} 篇文章')

    # 2. 抓取 arXiv
    print('\n[2/5] 抓取 arXiv 论文...')
    arxiv_articles = fetch_arxiv(ARXIV_CATEGORIES, ARXIV_MAX_RESULTS)
    print(f'  [OK] arXiv 共抓取 {len(arxiv_articles)} 篇论文')

    # 3. 抓取 GitHub Trending
    print('\n[3/5] 抓取 GitHub Trending...')
    github_repos = fetch_github_trending()
    print(f'  [OK] GitHub Trending 共抓取 {len(github_repos)} 个仓库')

    # 4. 合并、去重、分类
    print('\n[4/5] 处理数据...')
    all_articles = rss_articles + arxiv_articles
    seen_titles = set()
    unique_articles = []
    for a in all_articles:
        t = a['title'].lower().strip()
        if t and t not in seen_titles:
            seen_titles.add(t)
            a['category'] = classify_category(a.get('title',''), a.get('summary',''), a.get('category',''))
            unique_articles.append(a)
    unique_articles.sort(key=lambda x: x.get('pub_date',''), reverse=True)
    print(f'  [OK] 去重后共 {len(unique_articles)} 篇文章')

    # 5. 构建 data.js 结构
    print('\n[5/5] 生成 data.js...')
    quick_news    = build_quick_news(unique_articles)
    carousel      = build_carousel_slides(unique_articles)
    llm_section   = build_llm_section(unique_articles)
    research_sec  = build_research_section(arxiv_articles, rss_articles)
    app_section   = build_application_section(unique_articles)
    ind_section   = build_industry_section(unique_articles)
    policy_sec    = build_policy_section()
    open_src      = build_open_source_section(github_repos)
    hot_rank      = build_sidebar_hot_rank(unique_articles)
    tags          = build_tags_cloud(unique_articles)
    search_data   = build_search_data(unique_articles, quick_news)

    # AI 工具（保留静态）
    ai_tools = [
        {'icon': '💬', 'name': 'ChatGPT', 'url': 'https://chat.openai.com'},
        {'icon': '🤖', 'name': 'Claude', 'url': 'https://claude.ai'},
        {'icon': '🔍', 'name': 'Perplexity', 'url': 'https://www.perplexity.ai'},
        {'icon': '🎨', 'name': 'Midjourney', 'url': 'https://www.midjourney.com'},
        {'icon': '🎵', 'name': 'Suno', 'url': 'https://suno.com'},
        {'icon': '🎬', 'name': 'Runway', 'url': 'https://runway.ml'},
        {'icon': '📝', 'name': 'Jasper', 'url': 'https://www.jasper.ai'},
        {'icon': '💻', 'name': 'Cursor', 'url': 'https://cursor.sh'},
    ]

    # 组装最终 JS
    js_content = _render_js({
        'carouselSlides': carousel,
        'quickNews': quick_news,
        'sections': {
            'llm': llm_section,
            'research': research_sec,
            'application': app_section,
            'industry': ind_section,
            'policy': policy_sec,
            'openSource': open_src,
        },
        'sidebarHotRank': hot_rank,
        'aiTools': ai_tools,
        'hotTags': tags,
        'searchData': search_data,
    })

    # 写入文件
    os.makedirs(os.path.dirname(OUTPUT_JS_PATH), exist_ok=True)
    with open(OUTPUT_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f'\n[OK] 完成！已写入 {OUTPUT_JS_PATH}')
    print(f'   - 轮播图:    {len(carousel)} 条')
    print(f'   - 快讯:      {len(quick_news)} 条')
    print(f'   - 大模型动态: {len(llm_section["items"])} 条')
    print(f'   - AI研究:    {len(research_sec["items"])} 条')
    print(f'   - AI应用:    {len(app_section["items"])} 条')
    print(f'   - 行业动态:  {len(ind_section["items"])} 条')
    print(f'   - 开源热榜:  {len(open_src["projects"])} 条')
    print(f'   - 侧栏热榜:  {len(hot_rank)} 条')
    print(f'   - 搜索索引:  {len(search_data)} 条')
    print(f'   - 标签云:    {len(tags)} 个')


def _render_js(data):
    """将 Python dict 渲染为合法的 JavaScript（var siteData = {...}）"""
    lines = []
    lines.append('/**')
    lines.append(' * =======================================')
    lines.append(' * AI全球资讯 - 数据文件（自动生成）')
    lines.append(f' * 生成时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append(' * 请勿手动编辑此文件，内容由 fetch_news.py 自动生成')
    lines.append(' * =======================================')
    lines.append(' */')
    lines.append('')
    lines.append('var siteData = ' + json.dumps(data, ensure_ascii=False, indent=4))
    lines.append('')
    return '\n'.join(lines)


if __name__ == '__main__':
    main()
