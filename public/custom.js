// 鲲鹏志 · Chainlit 自定义注入脚本
(function() {
    console.log('鲲鹏志: custom.js 已加载');

    function ready(fn) {
        if (document.readyState !== 'loading') {
            setTimeout(fn, 0);
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    // ─── 1. 左右看板 ───────────────────────────────
    function injectSidebars() {
        if (document.getElementById('left-sidebar')) return;
        var left = document.createElement('div');
        left.id = 'left-sidebar';
        left.style.cssText = 'position:fixed;left:0;top:0;width:240px;height:100%;z-index:9990;';
        left.innerHTML = '<iframe src="/left-board" style="width:100%;height:100%;border:none;"></iframe>';
        document.body.appendChild(left);
        var right = document.createElement('div');
        right.id = 'right-sidebar';
        right.style.cssText = 'position:fixed;right:0;top:0;width:240px;height:100%;z-index:9990;';
        right.innerHTML = '<iframe src="/bagua" style="width:100%;height:100%;border:none;"></iframe>';
        document.body.appendChild(right);
        console.log('鲲鹏志: 左右面板注入完成');
    }

    // ─── 2. 浮动 Q&A 按钮 ─────────────────────────
    var qaLoaded = false;
    var qaTriggerEl = null;

    function loadQAWidget() {
        if (qaLoaded) return;
        qaLoaded = true;

        // 先加载 Google 脚本，加载完后再创建元素
        var s = document.createElement('script');
        s.src = 'https://cloud.google.com/ai/gen-app-builder/client?hl=zh_CN';
        s.async = true;

        s.onload = function() {
            console.log('鲲鹏志: Google Widget 脚本已加载');
            // 脚本已加载，现在创建 widget 元素
            var w = document.createElement('gen-search-widget');
            w.setAttribute('configId', '52a37158-b391-4d50-a881-93cfd950cafc');
            w.setAttribute('triggerId', 'qaBtn');
            w.style.display = 'none';
            document.body.appendChild(w);

            // 创建 trigger 元素
            qaTriggerEl = document.createElement('button');
            qaTriggerEl.id = 'qaBtn';
            qaTriggerEl.style.display = 'none';
            document.body.appendChild(qaTriggerEl);

            // 激活按钮
            var btn = document.getElementById('qa-float-btn');
            if (btn) {
                btn.onclick = function() {
                    console.log('鲲鹏志: Q&A 按钮被点击');
                    document.getElementById('qaBtn').click();
                };
                btn.style.cursor = 'pointer';
                btn.title = '搜鲲鹏志知识库';
                console.log('鲲鹏志: Q&A 按钮已激活');
            }
        };

        s.onerror = function() {
            console.error('鲲鹏志: Google Widget 脚本加载失败');
        };

        document.head.appendChild(s);
        console.log('鲲鹏志: 开始加载 Google Widget 脚本...');
    }

    function injectQAButton() {
        if (document.getElementById('qa-float-btn')) return;

        // 先创建按钮（灰色待激活状态）
        var btn = document.createElement('div');
        btn.id = 'qa-float-btn';
        btn.textContent = '🔍';
        btn.style.cssText = 'position:fixed;bottom:100px;right:270px;z-index:9999;width:48px;height:48px;border-radius:50%;background:#6b7280;color:#fff;font-size:20px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,0,0,0.3);border:none;user-select:none;transition:background 0.3s;';
        document.body.appendChild(btn);
        console.log('鲲鹏志: Q&A 按钮已创建（待激活）');

        // 开始加载 Widget 脚本
        loadQAWidget();
    }

    // ─── 3. 主注入逻辑 ─────────────────────────
    ready(function() {
        function tryInject() {
            if (!document.body) { setTimeout(tryInject, 100); return; }
            injectSidebars();
            injectQAButton();
            var dot = document.createElement('div');
            dot.id = 'script-test-dot';
            dot.style.cssText = 'position:fixed;top:5px;left:5px;z-index:99999;width:8px;height:8px;background:lime;border-radius:50%;';
            document.body.appendChild(dot);
            console.log('鲲鹏志: 所有注入完成 ✅');
        }
        tryInject();
    });
})();
