/* ========================================
   AI全球资讯 - 交互逻辑
   ======================================== */

document.addEventListener('DOMContentLoaded', function() {

    // ========================================
    // 0. 动态内容渲染（从 data.js 读取数据）
    // ========================================
    if (typeof ContentRenderer !== 'undefined') {
        ContentRenderer.renderAll();
    }

    // ========================================
    // 1. 当前日期显示
    // ========================================
    function updateDate() {
        const now = new Date();
        const options = {
            year: 'numeric', month: 'long', day: 'numeric',
            weekday: 'long'
        };
        const dateEl = document.getElementById('current-date');
        if (dateEl) {
            dateEl.textContent = now.toLocaleDateString('zh-CN', options);
        }
    }
    updateDate();

    // ========================================
    // 2. 轮播图功能
    // ========================================
    const carousel = document.getElementById('carousel');
    if (carousel) {
        const slides = carousel.querySelectorAll('.carousel-slide');
        const dots = document.querySelectorAll('#carouselDots .dot');
        const prevBtn = document.getElementById('carouselPrev');
        const nextBtn = document.getElementById('carouselNext');
        let currentSlide = 0;
        let autoPlayTimer = null;
        const TOTAL_SLIDES = slides.length;

        function goToSlide(index) {
            // 边界处理
            if (index < 0) index = TOTAL_SLIDES - 1;
            if (index >= TOTAL_SLIDES) index = 0;

            slides.forEach(s => s.classList.remove('active'));
            dots.forEach(d => d.classList.remove('active'));

            slides[index].classList.add('active');
            dots[index].classList.add('active');
            currentSlide = index;
        }

        function nextSlide() { goToSlide(currentSlide + 1); }
        function prevSlideFn() { goToSlide(currentSlide - 1); }

        function startAutoPlay() {
            stopAutoPlay();
            autoPlayTimer = setInterval(nextSlide, 5000);
        }

        function stopAutoPlay() {
            if (autoPlayTimer) {
                clearInterval(autoPlayTimer);
                autoPlayTimer = null;
            }
        }

        // 按钮事件
        if (prevBtn) prevBtn.addEventListener('click', function() {
            prevSlideFn();
            startAutoPlay();
        });
        if (nextBtn) nextBtn.addEventListener('click', function() {
            nextSlide();
            startAutoPlay();
        });

        // 圆点导航
        dots.forEach(function(dot, idx) {
            dot.addEventListener('click', function() {
                goToSlide(idx);
                startAutoPlay();
            });
        });

        // 鼠标悬停暂停自动播放
        carousel.addEventListener('mouseenter', stopAutoPlay);
        carousel.addEventListener('mouseleave', startAutoPlay);

        // 触摸滑动支持（移动端）
        let touchStartX = 0;
        let touchEndX = 0;

        carousel.addEventListener('touchstart', function(e) {
            touchStartX = e.changedTouches[0].screenX;
            stopAutoPlay();
        }, { passive: true });

        carousel.addEventListener('touchend', function(e) {
            touchEndX = e.changedTouches[0].screenX;
            var diff = touchStartX - touchEndX;
            if (Math.abs(diff) > 50) {
                if (diff > 0) nextSlide();
                else prevSlideFn();
            }
            startAutoPlay();
        }, { passive: true });

        startAutoPlay();
    }

    // ========================================
    // 3. 搜索功能
    // ========================================
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const searchModal = document.getElementById('searchModal');
    const modalSearchInput = document.getElementById('modalSearchInput');
    const closeSearchModal = document.getElementById('closeSearchModal');
    const searchResults = document.getElementById('searchResults');

    // 搜索数据源 - 优先使用 data.js 的数据
    var searchData = (typeof window._searchDataSource !== 'undefined' && window._searchDataSource.length > 0)
        ? window._searchDataSource
        : [
        { title: 'OpenAI发布GPT-5：多模态推理能力实现质的飞跃', category: '大模型动态', tag: 'GPT', snippet: 'GPT-5在数学推理、代码生成、科学分析等任务上展现出前所未有的能力，支持原生多模态输入输出。' },
        { title: 'Google DeepMind Gemini 3 Pro：首个通过图灵测试完整版的大模型', category: '大模型动态', tag: 'Gemini', snippet: 'Gemini 3 Pro在多项基准测试中刷新纪录，长上下文窗口扩展至2000万token。' },
        { title: 'Anthropic Claude 4 Opus：安全对齐与能力边界的新探索', category: '大模型动态', tag: 'Claude', snippet: 'Claude 4 Opus引入Constitutional AI 3.0架构，在保持高度安全性的同时，推理速度提升300%。' },
        { title: '2026年Q1全球AI投资超800亿美元，创历史新高', category: '行业动态', tag: '融资', snippet: '据VentureBeat数据，今年第一季度AI领域融资总额达823亿美元。' },
        { title: 'Meta发布Llama 5 400B参数开源模型，性能对标GPT-5', category: '大模型动态', tag: '开源', snippet: 'Llama 5完全开源，405B参数版本性能在多项基准上接近或超越闭源竞品。' },
        { title: '英伟达RTX 5090 AI算力卡正式发售，显存达64GB GDDR7', category: '行业动态', tag: '硬件', snippet: 'RTX 5090搭载全新Blackwell架构，AI推理性能较上一代提升3倍。' },
        { title: '字节跳动Seedance 2.0视频生成模型开放API调用', category: 'AI应用', tag: '视频生成', snippet: 'Seedance 2.0支持最长2分钟的高质量视频生成，画面连贯性大幅提升。' },
        { title: '欧盟《AI法案》全面生效，违规最高罚款全球营收6%', category: '政策法规', tag: '监管', snippet: '欧盟AI Act是全球首部综合性AI监管法规，对高风险AI系统提出严格要求。' },
        { title: '阿里通义千问Max 3.0上线，支持100种语言实时翻译', category: '大模型动态', tag: '国产大模型', snippet: '通义千问Max 3.0在多语言能力和中文理解方面达到业界领先水平。' },
        { title: '斯坦福大学发布WorldSim：首个数字孪生世界模拟器', category: 'AI研究', tag: '世界模型', snippet: 'WorldSim能够高精度模拟物理世界规律，为机器人训练和自动驾驶提供新范式。' },
        { title: '苹果WWDC 2026官宣：iOS 26将集成全新Apple Intelligence 3', category: '行业动态', tag: '产品发布', snippet: 'Apple Intelligence 3将深度整合Siri、设备端AI能力和跨设备协作功能。' },
        { title: 'OpenAI宣布ChatGPT月活用户突破15亿，企业版收入翻倍', category: '行业动态', tag: '产品数据', snippet: 'ChatGPT Enterprise版本受到企业客户热烈欢迎，ARR突破20亿美元。' },
        { title: 'Scaling Laws 2.0：当参数量不再是唯一指标', category: 'AI研究', tag: '论文解读', snippet: 'MIT、Stanford和DeepMind联合团队在Nature发表重磅论文，挑战传统假设。' },
        { title: 'ICML 2026最佳论文：Neural Architecture Search进入毫秒时代', category: 'AI研究', tag: '学术会议', snippet: '清华-UC Berkeley联合团队提出的FlashNAS方法将架构搜索时间从数天缩短至毫秒级。' },
        { title: 'LeCun团队JEPA架构实现物理世界精确预测', category: 'AI研究', tag: '技术报告', snippet: 'JEPA最新研究成果在视频理解和物理仿真方面取得重大突破。' },
        { title: 'Cursor IDE日活破千万：AI正在重新定义软件开发', category: 'AI应用', tag: '开发工具', snippet: 'Cursor IDE凭借强大的代码补全和重构能力，已成为开发者首选的编程环境之一。' },
        { title: 'Suno V4音乐生成模型：从Demo到商业发行的跨越', category: 'AI应用', tag: '音乐生成', snippet: 'Suno V4生成的音乐质量已达到商业发行标准，多家唱片公司开始采用。' },
        { title: 'Pika 3.0视频生成：5秒生成好莱坞级别特效镜头', category: 'AI应用', tag: '视频生成', snippet: 'Pika 3.0引入物理引擎模拟，视频中的光影和运动效果更加真实。' },
        { title: 'Perplexity搜索市场份额达22%，Google首次感到威胁', category: 'AI应用', tag: 'AI搜索', snippet: '基于AI的回答引擎Perplexity正快速蚕食传统搜索引擎的市场份额。' },
        { title: 'Harvey AI获纽约州律师牌照：AI法律助手合法化里程碑', category: 'AI应用', tag: '法律AI', snippet: '这是AI法律助手首次获得美国州级律师执业许可，具有标志性意义。' }
    ];

    function openSearchModal() {
        if (searchModal) {
            searchModal.classList.add('active');
            document.body.style.overflow = 'hidden';
            setTimeout(function() {
                if (modalSearchInput) modalSearchInput.focus();
            }, 100);
        }
    }

    function closeSearchModalFn() {
        if (searchModal) {
            searchModal.classList.remove('active');
            document.body.style.overflow = '';
            if (modalSearchInput) modalSearchInput.value = '';
            resetSearchResults();
        }
    }

    function resetSearchResults() {
        if (searchResults) {
            searchResults.innerHTML = '<p class="search-hint">输入关键词开始搜索...</p>';
        }
    }

    function performSearch(query) {
        query = query.trim().toLowerCase();
        if (!query) {
            resetSearchResults();
            return;
        }

        var results = searchData.filter(function(item) {
            return item.title.toLowerCase().indexOf(query) !== -1 ||
                   item.category.toLowerCase().indexOf(query) !== -1 ||
                   item.tag.toLowerCase().indexOf(query) !== -1 ||
                   item.snippet.toLowerCase().indexOf(query) !== -1;
        });

        if (results.length === 0) {
            searchResults.innerHTML =
                '<div style="text-align:center;padding:30px;color:var(--text-tertiary);">' +
                '<div style="font-size:48px;margin-bottom:12px;">🔍</div>' +
                '<p>未找到与 "<strong>' + escapeHtml(query) + '</strong>" 相关的结果</p>' +
                '<p style="font-size:13px;margin-top:8px;">试试其他关键词？</p></div>';
            return;
        }

        var html = '';
        results.forEach(function(item, idx) {
            var highlightedTitle = highlightMatch(item.title, query);
            var highlightedSnippet = highlightMatch(item.snippet, query);

            html += '<div class="search-result-item" data-index="' + idx + '">' +
                '<div class="result-category">' + escapeHtml(item.category) + '</div>' +
                '<div class="result-title">' + highlightedTitle + '</div>' +
                '<div class="result-snippet">' + highlightedSnippet + '</div>' +
                '</div>';
        });

        html += '<div style="padding:16px 0;text-align:center;font-size:12px;color:var(--text-tertiary);">' +
            '找到 <strong>' + results.length + '</strong> 条相关结果</div>';

        searchResults.innerHTML = html;
    }

    function highlightMatch(text, query) {
        var escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        var regex = new RegExp('(' + escapedQuery + ')', 'gi');
        return text.replace(regex, '<mark style="background:rgba(99,102,241,0.2);color:var(--primary-dark);padding:0 2px;border-radius:2px;">$1</mark>');
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 搜索事件绑定
    if (searchInput) searchInput.addEventListener('focus', openSearchModal);
    if (searchBtn) searchBtn.addEventListener('click', openSearchModal);

    if (modalSearchInput) {
        modalSearchInput.addEventListener('input', function(e) {
            performSearch(e.target.value);
        });
        modalSearchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeSearchModalFn();
        });
    }

    if (closeSearchModal) closeSearchModal.addEventListener('click', closeSearchModalFn);
    if (searchModal) {
        searchModal.addEventListener('click', function(e) {
            if (e.target === searchModal) closeSearchModalFn();
        });
    }

    // 全局快捷键 Ctrl+K 打开搜索
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openSearchModal();
        }
        if (e.key === 'Escape') {
            closeSearchModalFn();
        }
    });

    // ========================================
    // 4. 二级分类Tab切换
    // ========================================
    var subNavTabs = document.querySelectorAll('#subNavTabs .sub-tab');
    subNavTabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            subNavTabs.forEach(function(t) { t.classList.remove('active'); });
            tab.classList.add('active');

            // 这里可以添加筛选逻辑
            var filter = this.getAttribute('data-filter');
            console.log('切换筛选:', filter);
        });
    });

    // ========================================
    // 5. 板块内Tab切换
    // ========================================
    var secTabs = document.querySelectorAll('.sec-tab');
    secTabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            var siblings = this.parentElement.querySelectorAll('.sec-tab');
            siblings.forEach(function(t) { t.classList.remove('active'); });
            this.classList.add('active');
        });
    });

    // ========================================
    // 6. 回到顶部按钮
    // ========================================
    var backToTop = document.getElementById('backToTop');
    if (backToTop) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 400) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });

        backToTop.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ========================================
    // 7. 移动端菜单
    // ========================================
    var mobileMenuToggle = document.getElementById('mobileMenuToggle');
    var mainNav = document.getElementById('mainNav');

    if (mobileMenuToggle && mainNav) {
        mobileMenuToggle.addEventListener('click', function() {
            mainNav.classList.toggle('open');
            var isOpen = mainNav.classList.contains('open');
            mobileMenuToggle.textContent = isOpen ? '✕' : '☰';
            document.body.style.overflow = isOpen ? 'hidden' : '';
        });

        // 下拉菜单点击展开
        var dropdownItems = mainNav.querySelectorAll('.has-dropdown');
        dropdownItems.forEach(function(item) {
            var link = item.querySelector(':scope > a');
            if (link) {
                link.addEventListener('click', function(e) {
                    if (window.innerWidth <= 768) {
                        e.preventDefault();
                        item.classList.toggle('open');
                        var arrow = this.querySelector('.arrow');
                        if (arrow) arrow.textContent = item.classList.contains('open') ? '▴' : '▾';
                    }
                });
            }
        });
    }

    // ========================================
    // 8. 导航栏滚动效果
    // ========================================
    var lastScrollY = 0;
    var header = document.querySelector('.main-header');

    window.addEventListener('scroll', function() {
        var scrollY = window.scrollY;

        // 导航栏阴影增强
        if (header) {
            if (scrollY > 10) {
                header.style.boxShadow = '0 4px 20px rgba(0,0,0,0.08)';
            } else {
                header.style.boxShadow = 'var(--shadow-sm)';
            }
        }

        lastScrollY = scrollY;
    });

    // ========================================
    // 9. 订阅表单交互
    // ========================================
    var subscribeForm = document.querySelector('.subscribe-form');
    if (subscribeForm) {
        subscribeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            var emailInput = this.querySelector('input[type="email"]');
            var btn = this.querySelector('.submit-btn, button[type="submit"]');

            if (emailInput && emailInput.value) {
                // 简单的前端验证
                var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(emailInput.value)) {
                    alert('请输入有效的邮箱地址');
                    return;
                }

                btn.textContent = '✓ 订阅成功！';
                btn.style.background = '#10b981';
                emailInput.disabled = true;
                btn.disabled = true;

                setTimeout(function() {
                    btn.textContent = '免费订阅';
                    btn.style.background = '';
                    emailInput.disabled = false;
                    btn.disabled = false;
                    emailInput.value = '';
                }, 3000);
            }
        });
    }

    // ========================================
    // 10. 快讯列表时间更新模拟
    // ========================================

    // 模拟快讯时间更新（每分钟）
    function simulateQuickNewsTime() {
        var quickNewsItems = document.querySelectorAll('#quickNewsList .quick-news-item .time');
        // 仅作为演示，实际项目中应通过后端API获取实时数据
    }

    // 每60秒检查一次
    setInterval(simulateQuickNewsTime, 60000);

    // ========================================
    // 11. 平滑滚动锚点导航
    // ========================================
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            var targetId = this.getAttribute('href');
            if (targetId === '#') return;

            var targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                var offsetTop = targetElement.offsetTop - 130; // 减去header高度
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });

                // 关闭移动端菜单
                if (mainNav) mainNav.classList.remove('open');
                if (mobileMenuToggle) mobileMenuToggle.textContent = '☰';
                document.body.style.overflow = '';
            }
        });
    });

    // ========================================
    // 12. 标签云点击统计（演示用）
    // ========================================
    document.querySelectorAll('#tagsCloud .tag-item').forEach(function(tag) {
        tag.addEventListener('click', function(e) {
            e.preventDefault();
            var keyword = this.textContent.trim();
            openSearchModal();
            if (modalSearchInput) {
                modalSearchInput.value = keyword;
                performSearch(keyword);
            }
        });
    });

    // ========================================
    // 14. 广告位关闭功能
    // ========================================
    document.querySelectorAll('.ad-close').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            var adSlot = this.closest('.ad-slot');
            var adBanner = this.closest('.ad-banner');

            // 添加淡出动画
            if (adBanner) {
                adBanner.style.transition = 'opacity 0.3s ease, max-height 0.3s ease, margin 0.3s ease';
                adBanner.style.opacity = '0';
                adBanner.style.maxHeight = '0';
                adBanner.style.marginTop = '0';
                adBanner.style.marginBottom = '0';
                adBanner.style.overflow = 'hidden';

                setTimeout(function() {
                    adBanner.style.display = 'none';
                }, 300);
            }
        });
    });

    // 广告位点击跳转
    document.querySelectorAll('.ad-placeholder').forEach(function(placeholder) {
        placeholder.addEventListener('click', function() {
            var link = this.querySelector('.ad-link');
            if (link && link.getAttribute('href') !== '#') {
                window.open(link.getAttribute('href'), '_blank', 'noopener,noreferrer');
            }
        });
    });

    // ========================================
    // 15. 新闻卡片点击效果
    // ========================================
    document.querySelectorAll('.news-card, .list-news-item, .policy-card').forEach(function(card) {
        card.addEventListener('click', function() {
            // 添加点击波纹效果
            this.style.transition = 'transform 0.1s ease';
            this.style.transform = 'scale(0.98)';
            var self = this;
            setTimeout(function() {
                self.style.transform = '';
            }, 100);
        });
    });

    // ========================================
    // 14. 页面加载完成提示
    // ========================================
    console.log('%c🤖 AI全球资讯网站已加载完成',
        'color:#6366f1; font-size:16px; font-weight:bold;');
    console.log('%c快捷键: Ctrl+K 打开搜索 | ESC 关闭弹窗',
        'color:#94a3b8; font-size:12px;');

});
