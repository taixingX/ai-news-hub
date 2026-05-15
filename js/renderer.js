/**
 * ========================================
 * AI全球资讯 - 动态渲染引擎
 * ========================================
 * 从 data.js 读取数据，动态渲染页面所有内容区块
 * 使用方法：在 main.js 之前引入此文件，DOMContentLoaded 时调用 renderAllContent()
 */

var ContentRenderer = (function() {

    /* ---------- 工具函数 ---------- */

    function esc(text) {
        if (!text) return '';
        var d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }

    function safeUrl(url) {
        if (url && url !== '#' && url.startsWith('http')) {
            return esc(url);
        }
        return '#';
    }

    /**
     * 渲染头条轮播图
     */
    function renderCarousel() {
        var inner = document.getElementById('carouselInner');
        var dotsContainer = document.getElementById('carouselDots');
        if (!inner || !dotsContainer || !siteData.carouselSlides) return;

        var slidesHtml = '';
        var dotsHtml = '';

        siteData.carouselSlides.forEach(function(slide, i) {
            var activeCls = i === 0 ? ' active' : '';
            slidesHtml +=
                '<a href="' + safeUrl(slide.url) + '" class="carousel-slide' + activeCls + '" style="--slide-bg: ' + slide.bg + ';"' + (slide.url ? ' target="_blank" rel="noopener"' : '') + '>' +
                    '<div class="slide-tag">' + esc(slide.tag) + '</div>' +
                    '<h2 class="slide-title">' + esc(slide.title) + '</h2>' +
                    '<p class="slide-summary">' + esc(slide.summary) + '</p>' +
                    '<div class="slide-meta">' +
                        '<span class="slide-source">来源：' + esc(slide.source) + '</span> ' +
                        '<span class="slide-time">' + esc(slide.time) + '</span> ' +
                        '<span class="slide-views">👁 ' + esc(slide.views) + '</span>' +
                    '</div>' +
                '</a>';
            dotsHtml += '<span class="dot' + activeCls + '"></span>';
        });

        inner.innerHTML = slidesHtml;
        dotsContainer.innerHTML = dotsHtml;
    }

    /**
     * 渲染快讯列表
     */
    function renderQuickNews() {
        var list = document.getElementById('quickNewsList');
        if (!list || !siteData.quickNews) return;

        var html = '';
        siteData.quickNews.forEach(function(item) {
            html += '<li class="quick-news-item' + (item.hot ? ' hot' : '') + '">' +
                '<span class="time">' + esc(item.time) + '</span> ' +
                '<a href="' + safeUrl(item.url) + '"' + (item.url ? ' target="_blank" rel="noopener"' : '') + '>' + esc(item.text) + '</a>' +
            '</li>';
        });
        list.innerHTML = html;
    }

    /**
     * 渲染大模型动态（网格卡片布局）
     */
    function renderLLMSection() {
        var container = document.getElementById('render-llm');
        if (!container || !siteData.sections.llm) return;

        var sec = siteData.sections.llm;
        var cardsHtml = '';

        sec.items.forEach(function(item) {
            if (item.featured) {
                cardsHtml +=
                    '<article class="news-card featured">' +
                        '<div class="news-card-image" style="background: ' + item.bg + ';">' +
                            '<div class="image-overlay"><span class="card-tag">' + esc(item.tag) + '</span></div>' +
                        '</div>' +
                        '<div class="news-card-body">' +
                            '<h3 class="news-card-title"><a href="' + safeUrl(item.url) + '"' + (item.url ? ' target="_blank" rel="noopener"' : '') + '>' + esc(item.title) + '</a></h3>' +
                            '<p class="news-card-desc">' + esc(item.desc) + '</p>' +
                            '<div class="news-card-footer">' +
                                '<span class="source">' + esc(item.source) + '</span> ' +
                                '<span class="time">' + esc(item.time) + '</span> ' +
                                '<span class="stats">👁 ' + esc(item.views) + ' 💬 ' + esc(item.comments) + '</span>' +
                            '</div>' +
                        '</div>' +
                    '</article>';
            } else {
                cardsHtml +=
                    '<article class="news-card" data-category="' + esc(item.category || '') + '">' +
                        '<div class="news-card-image" style="background: ' + item.bg + ';"></div>' +
                        '<div class="news-card-body">' +
                            '<h3 class="news-card-title"><a href="' + safeUrl(item.url) + '"' + (item.url ? ' target="_blank" rel="noopener"' : '') + '>' + esc(item.title) + '</a></h3>' +
                            '<div class="news-card-footer">' +
                                '<span class="source">' + esc(item.source) + '</span> ' +
                                '<span class="time">' + esc(item.time) + '</span> ' +
                                '<span class="stats">👁 ' + esc(item.views) + ' 💬 ' + esc(item.comments || '0') + '</span>' +
                            '</div>' +
                        '</div>' +
                    '</article>';
            }
        });

        container.innerHTML = '<div class="news-grid">' + cardsHtml + '</div>';
    }

    /**
     * 渲染AI研究（列表布局）
     */
    function renderResearchSection() {
        var container = document.getElementById('render-research');
        if (!container || !siteData.sections.research) return;

        var items = siteData.sections.research.items;
        var html = '';

        items.forEach(function(item) {
            html +=
                '<article class="list-news-item" data-category="' + esc(item.category || '') + '">' +
                    '<div class="list-news-thumb" style="background: ' + item.bg + ';"></div>' +
                    '<div class="list-news-info">' +
                        '<h3><a href="' + safeUrl(item.url) + '"' + (item.url ? ' target="_blank" rel="noopener"' : '') + '>' + esc(item.title) + '</a></h3>' +
                        (item.desc ? '<p class="desc">' + esc(item.desc) + '</p>' : '') +
                        '<div class="meta">' +
                            (item.tag ? '<span class="tag ' + esc(item.tagClass || '') + '">' + esc(item.tag) + '</span>' : '') +
                            '<span class="source">' + esc(item.source) + '</span> ' +
                            '<span class="time">' + esc(item.time) + '</span>' +
                        '</div>' +
                    '</div>' +
                '</article>';
        });

        container.innerHTML = '<div class="news-list-layout">' + html + '</div>';
    }

    /**
     * 渲染AI应用（简单排行列表）
     */
    function renderApplicationList() {
        var container = document.getElementById('render-application');
        if (!container || !siteData.sections.application) return;

        var html = '';
        siteData.sections.application.items.forEach(function(item) {
            var rankCls = item.rank <= 3 ? ' rank-' + item.rank : '';
            html +=
                '<article class="simple-news-item">' +
                    '<h4><a href="' + safeUrl(item.url) + '"' + (item.url ? ' target="_blank" rel="noopener"' : '') + '><span class="rank-badge' + rankCls + '">' + item.rank + '</span> ' + esc(item.title) + '</a></h4>' +
                    '<span class="item-time">' + esc(item.time) + '</span>' +
                '</article>';
        });
        container.innerHTML = '<div class="simple-news-list">' + html + '</div>';
    }

    /**
     * 渲染行业动态（简单列表）
     */
    function renderIndustryList() {
        var container = document.getElementById('render-industry');
        if (!container || !siteData.sections.industry) return;

        var html = '';
        siteData.sections.industry.items.forEach(function(item) {
            html +=
                '<article class="simple-news-item">' +
                    '<h4><a href="' + safeUrl(item.url) + '"' + (item.url ? ' target="_blank" rel="noopener"' : '') + '>' + esc(item.title) + '</a></h4>' +
                    '<span class="item-time">' + esc(item.time) + '</span>' +
                '</article>';
        });
        container.innerHTML = '<div class="simple-news-list">' + html + '</div>';
    }

    /**
     * 渲染政策法规卡片
     */
    function renderPolicyCards() {
        var container = document.getElementById('render-policy');
        if (!container || !siteData.sections.policy) return;

        var html = '';
        siteData.sections.policy.items.forEach(function(item) {
            html +=
                '<article class="policy-card">' +
                    '<div class="policy-flag">' + esc(item.flag) + '</div>' +
                    '<div class="policy-body">' +
                        '<h4><a href="#">' + esc(item.title) + '</a></h4>' +
                        '<p>' + esc(item.desc) + '</p>' +
                        '<div class="policy-meta">' +
                            '<span class="policy-date">' + esc(item.date) + '</span> ' +
                            '<span class="policy-level">' + esc(item.level) + '</span>' +
                        '</div>' +
                    '</div>' +
                '</article>';
        });
        container.innerHTML = '<div class="policy-cards">' + html + '</div>';
    }

    /**
     * 渲染开源项目热榜表格
     */
    function renderOpenSourceTable() {
        var container = document.getElementById('render-openSource');
        if (!container || !siteData.sections.openSource) return;

        var proj = siteData.sections.openSource;
        var rowsHtml = '';

        proj.projects.forEach(function(p) {
            rowsHtml +=
                '<tr>' +
                    '<td class="rank-cell">' + p.rank + '</td>' +
                    '<td><a href="' + safeUrl(p.url) + '"' + (p.url ? ' target="_blank" rel="noopener"' : '') + ' class="project-name">' + esc(p.name) + '</a></td>' +
                    '<td class="project-desc">' + esc(p.desc) + '</td>' +
                    '<td><span class="lang-tag ' + esc(p.langClass) + '">' + esc(p.lang) + '</span></td>' +
                    '<td class="stars-cell">' + esc(p.stars) + '</td>' +
                '</tr>';
        });

        container.innerHTML =
            '<div class="project-table-wrapper">' +
                '<table class="project-table">' +
                    '<thead><tr><th>#</th><th>项目名称</th><th>简介</th><th>语言</th><th>⭐ 今日</th></tr></thead>' +
                    '<tbody>' + rowsHtml + '</tbody>' +
                '</table>' +
            '</div>';
    }

    /**
     * 渲染侧栏热榜 TOP10
     */
    function renderSidebarHotRank() {
        var container = document.getElementById('render-hotRank');
        if (!container || !siteData.sidebarHotRank) return;

        var html = '';
        siteData.sidebarHotRank.forEach(function(item) {
            var cls = item.top3 ? ' top3' : '';
            html +=
                '<li class="hot-item' + cls + '">' +
                    '<a href="' + safeUrl(item.url) + '"' + (item.url ? ' target="_blank" rel="noopener"' : '') + '><span class="rank-num">' + item.rank + '</span> ' + esc(item.title) + '</a>' +
                    (item.heat ? '<span class="heat">' + esc(item.heat) + '</span>' : '') +
                '</li>';
        });
        container.innerHTML = '<ol class="hot-rank-list">' + html + '</ol>';
    }

    /**
     * 渲染AI工具箱
     */
    function renderAITools() {
        var container = document.getElementById('render-tools');
        if (!container || !siteData.aiTools) return;

        var html = '';
        siteData.aiTools.forEach(function(tool) {
            html += '<a href="#" class="tool-item"><span class="tool-icon">' + esc(tool.icon) + '</span><span class="tool-name">' + esc(tool.name) + '</span></a>';
        });
        container.innerHTML = '<div class="tools-grid">' + html + '</div>';
    }

    /**
     * 渲染标签云
     */
    function renderTagsCloud() {
        var container = document.getElementById('render-tags');
        if (!container || !siteData.hotTags) return;

        var html = '';
        siteData.hotTags.forEach(function(tag) {
            html += '<a href="#" class="tag-item ' + tag.size + '">' + esc(tag.text) + '</a>';
        });
        container.innerHTML = '<div class="tags-cloud" id="tagsCloud">' + html + '</div>';
    }

    /* ---------- 公开 API ---------- */

    return {
        /**
         * 渲染全部内容区块
         */
        renderAll: function() {
            renderCarousel();
            renderQuickNews();
            renderLLMSection();
            renderResearchSection();
            renderApplicationList();
            renderIndustryList();
            renderPolicyCards();
            renderOpenSourceTable();
            renderSidebarHotRank();
            renderAITools();
            renderTagsCloud();

            // 同步搜索数据源
            if (typeof siteData !== 'undefined' && siteData.searchData) {
                window._searchDataSource = siteData.searchData;
            }
        },

        /** 单独渲染某个区块（供按需更新使用） */
        renderCarousel: renderCarousel,
        renderQuickNews: renderQuickNews,
        renderLLM: renderLLMSection,
        renderResearch: renderResearchSection,
        renderApplication: renderApplicationList,
        renderIndustry: renderIndustryList,
        renderPolicy: renderPolicyCards,
        renderOpenSource: renderOpenSourceTable,
        renderHotRank: renderSidebarHotRank,
        renderTools: renderAITools,
        renderTags: renderTagsCloud
    };

})();
