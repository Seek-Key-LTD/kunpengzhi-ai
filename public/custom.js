// 鲲鹏志 · Chainlit 自定义注入 (v9 — 🔍 弹出搜索页)
(function(){
    console.log('[鲲鹏志] v9');

    function waitBody(fn) {
        if (document.body) { fn(); return; }
        var i = setInterval(function() {
            if (document.body) { clearInterval(i); fn(); }
        }, 100);
    }

    waitBody(function(){
        // ===== 1. 左右固定侧栏 =====
        function makeSidebar(id, src, pos) {
            if (document.getElementById(id)) return;
            var el = document.createElement('div');
            el.id = id;
            el.style.cssText = 'position:fixed;top:0;bottom:0;z-index:9990;background:#0b0f19;overflow:hidden;box-shadow:0 0 24px rgba(0,0,0,0.5);';
            el.style[pos] = '0';
            if (pos === 'left') el.style.borderRight = '1px solid rgba(255,255,255,0.08)';
            else el.style.borderLeft = '1px solid rgba(255,255,255,0.08)';
            el.innerHTML = '<iframe src="'+src+'" style="width:100%;height:100%;border:none;"></iframe>';
            document.body.appendChild(el);
        }
        makeSidebar('kz-left', '/left-board', 'left');
        makeSidebar('kz-right', '/bagua', 'right');

        // ===== 2. root 不推挤 =====
        var root = document.getElementById('root');
        if (root) root.style.cssText += ';margin-left:28.33%!important;margin-right:0!important;max-width:33.33%!important;';

        // ===== 3. 🔍 放大镜 =====
        if (document.getElementById('kz-search-btn')) return;

        // 🔍 按钮
        var btn = document.createElement('button');
        btn.id = 'kz-search-btn';
        btn.textContent = '🔍';
        btn.title = '搜鲲鹏志知识库';
        btn.style.cssText = 'position:fixed!important;bottom:30px!important;right:30px!important;z-index:999998!important;width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,#f59e0b,#ef4444);color:#fff;font-size:24px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 16px rgba(0,0,0,0.4);border:2px solid rgba(255,255,255,0.3);cursor:pointer;user-select:none;transition:transform .15s,box-shadow .15s;';
        document.body.appendChild(btn);

        // hover 动效
        btn.onmouseenter = function(){ this.style.transform='scale(1.1)'; this.style.boxShadow='0 6px 24px rgba(0,0,0,0.6)'; };
        btn.onmouseleave = function(){ this.style.transform='scale(1)'; this.style.boxShadow='0 4px 16px rgba(0,0,0,0.4)'; };

        // 点击 → 弹出搜索页面（弹窗/浮层）
        btn.addEventListener('click', function(e){
            if (this.dataset.drag === '1') { this.dataset.drag = '0'; return; }
            console.log('[鲲鹏志] 🔍 打开搜索页');

            // 创建半透明遮罩 + 搜索 iframe 浮层
            var overlay = document.createElement('div');
            overlay.id = 'kz-search-overlay';
            overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:999999;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;';

            // 浮层卡片
            var panel = document.createElement('div');
            panel.style.cssText = 'width:90%;max-width:800px;height:80%;background:#0f172a;border-radius:16px;border:1px solid rgba(255,255,255,0.1);box-shadow:0 24px 64px rgba(0,0,0,0.8);overflow:hidden;display:flex;flex-direction:column;position:relative;';

            // 顶栏
            var header = document.createElement('div');
            header.style.cssText = 'height:40px;display:flex;align-items:center;justify-content:space-between;padding:0 16px;background:rgba(255,255,255,0.04);border-bottom:1px solid rgba(255,255,255,0.06);flex-shrink:0;';
            header.innerHTML = '<span style="color:rgba(255,255,255,0.6);font-size:13px;">🔍 鲲鹏志·知识库</span>';
            var closeBtn = document.createElement('span');
            closeBtn.textContent = '✕';
            closeBtn.style.cssText = 'color:rgba(255,255,255,0.4);cursor:pointer;font-size:18px;padding:4px 8px;border-radius:4px;';
            closeBtn.onmouseenter = function(){ this.style.color = '#fff'; };
            closeBtn.onmouseleave = function(){ this.style.color = 'rgba(255,255,255,0.4)'; };
            closeBtn.onclick = function(){ overlay.remove(); };
            header.appendChild(closeBtn);
            panel.appendChild(header);

            // iframe（加载 kunpengzhi-qa.html，这个页面 widget 配置是对的）
            var iframe = document.createElement('iframe');
            iframe.src = '/kunpengzhi-qa.html';
            iframe.style.cssText = 'flex:1;width:100%;border:none;';
            panel.appendChild(iframe);

            overlay.appendChild(panel);
            document.body.appendChild(overlay);

            // 点遮罩关闭
            overlay.addEventListener('click', function(e){
                if (e.target === overlay) overlay.remove();
            });
        });

        // 可拖拽
        (function(){
            var drag = false, ox, oy, sx, sy, moved = false;
            btn.addEventListener('mousedown', function(e){
                drag = false; moved = false;
                ox = e.clientX - btn.getBoundingClientRect().left;
                oy = e.clientY - btn.getBoundingClientRect().top;
                sx = e.clientX; sy = e.clientY;
                btn.style.transition = 'none';
            });
            document.addEventListener('mousemove', function(e){
                if (ox === undefined) return;
                var dx = e.clientX - sx, dy = e.clientY - sy;
                if (!moved && (Math.abs(dx) > 3 || Math.abs(dy) > 3)) {
                    moved = true; drag = true;
                }
                if (!drag) return;
                btn.style.left = (e.clientX - ox) + 'px';
                btn.style.top = (e.clientY - oy) + 'px';
                btn.style.right = 'auto';
                btn.style.bottom = 'auto';
            });
            document.addEventListener('mouseup', function(){
                if (drag) btn.style.transition = 'transform .15s,box-shadow .15s';
                ox = undefined; oy = undefined;
                if (moved) {
                    btn.dataset.drag = '1';
                    setTimeout(function(){ btn.dataset.drag = '0'; }, 400);
                }
                drag = false; moved = false;
            });
        })();

        console.log('[鲲鹏志] v9 注入完成 ✅');
    });
})();
