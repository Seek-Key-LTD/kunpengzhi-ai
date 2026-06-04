// 鲲鹏志 · Chainlit 自定义注入脚本
(function() {
    'use strict';
    console.log('[鲲鹏志] custom.js 已加载');

    var injected = false;

    function doInject() {
        if (injected) return;
        if (!document.body) { setTimeout(doInject, 200); return; }

        // 测试标记
        var dot = document.createElement('div');
        dot.id = 'kz-dot';
        dot.textContent = '✅';
        dot.style.cssText = 'position:fixed;top:2px;left:2px;z-index:999999;font-size:10px;background:rgba(0,255,0,0.8);padding:2px 4px;border-radius:3px;';
        document.body.appendChild(dot);

        // 左右面板
        var l = document.createElement('div');
        l.id = 'kz-left';
        l.className = 'fixed-sidebar';
        l.innerHTML = '<iframe src="/left-board" style="width:100%;height:100%;border:none;" title="left"></iframe>';
        document.body.appendChild(l);

        var r = document.createElement('div');
        r.id = 'kz-right';
        r.className = 'fixed-sidebar';
        r.innerHTML = '<iframe src="/bagua" style="width:100%;height:100%;border:none;" title="right"></iframe>';
        document.body.appendChild(r);

        // 加载 Google Widget
        var gs = document.createElement('script');
        gs.src = 'https://cloud.google.com/ai/gen-app-builder/client?hl=zh_CN';
        gs.onload = function() {
            console.log('[鲲鹏志] Google Widget 已就绪');
            var gw = document.createElement('gen-search-widget');
            gw.setAttribute('configId', '52a37158-b391-4d50-a881-93cfd950cafc');
            gw.setAttribute('triggerId', 'kz-search-trigger');
            gw.style.display = 'none';
            document.body.appendChild(gw);

            var tr = document.createElement('span');
            tr.id = 'kz-search-trigger';
            tr.style.display = 'none';
            document.body.appendChild(tr);

            var btn = document.getElementById('kz-search-btn');
            if (btn) {
                btn.onclick = function() {
                    var t = document.getElementById('kz-search-trigger');
                    if (t) t.click();
                };
                btn.style.background = 'linear-gradient(135deg,#f59e0b,#ef4444)';
                btn.title = '搜鲲鹏志知识库';
                console.log('[鲲鹏志] 🔍 按钮已激活');
            }
        };
        document.head.appendChild(gs);

        // 🔍 按钮（默认灰色）
        var btn = document.createElement('div');
        btn.id = 'kz-search-btn';
        btn.textContent = '🔍';
        btn.style.cssText = 'position:fixed;bottom:100px;right:270px;z-index:9999;width:48px;height:48px;border-radius:50%;background:#6b7280;color:#fff;font-size:20px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,0,0,0.3);border:none;user-select:none;cursor:default;';
        document.body.appendChild(btn);

        injected = true;
        console.log('[鲲鹏志] 全部注入完成 ✅');
    }

    // 等 window load 确保 React 已挂载
    window.addEventListener('load', doInject);
    // 兜底：如果 load 已触发
    if (document.readyState === 'complete') doInject();
})();
