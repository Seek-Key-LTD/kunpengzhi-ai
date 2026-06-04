// 鲲鹏志 · Chainlit 自定义注入 (v5 — 纯悬浮)
(function(){
    console.log('[鲲鹏志] v5 脚本开始');

    function waitBody(fn) {
        if (document.body) { fn(); return; }
        var i = setInterval(function() {
            if (document.body) { clearInterval(i); fn(); }
        }, 100);
    }

    waitBody(function(){
        console.log('[鲲鹏志] body 存在');

        // ===== 0. root 不推挤 =====
        var root = document.getElementById('root');
        if (root) {
            root.style.cssText += ';margin-left:0!important;margin-right:0!important;max-width:100%!important;';
        }

        // ===== 可拖拽悬浮窗引擎 =====
        function makeFloater(id, opts) {
            opts = opts || {};
            var w = opts.width || 280;
            var h = opts.height || 400;
            var title = opts.title || '';
            var content = opts.content || '';

            var el = document.createElement('div');
            el.id = id;
            el.style.cssText = 'position:fixed;z-index:9990;width:'+w+'px;height:'+h+'px;background:#0b0f19;border:1px solid rgba(255,255,255,0.1);border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,0.6);overflow:hidden;display:flex;flex-direction:column;';

            // 标题栏（拖拽把手）
            var bar = document.createElement('div');
            bar.style.cssText = 'height:28px;background:rgba(255,255,255,0.06);display:flex;align-items:center;padding:0 10px;cursor:grab;user-select:none;flex-shrink:0;border-bottom:1px solid rgba(255,255,255,0.06);';
            var barLabel = document.createElement('span');
            barLabel.textContent = title;
            barLabel.style.cssText = 'color:rgba(255,255,255,0.5);font-size:12px;flex:1;';
            bar.appendChild(barLabel);
            // 最小化按钮
            var minBtn = document.createElement('span');
            minBtn.textContent = '—';
            minBtn.style.cssText = 'color:rgba(255,255,255,0.3);cursor:pointer;padding:0 6px;font-size:14px;';
            minBtn.onclick = function(e){
                e.stopPropagation();
                el.dataset.minimized = el.dataset.minimized === '1' ? '0' : '1';
                var body = el.querySelector('.kz-floater-body');
                if (body) body.style.display = el.dataset.minimized === '1' ? 'none' : 'flex';
                minBtn.textContent = el.dataset.minimized === '1' ? '□' : '—';
            };
            bar.appendChild(minBtn);
            el.appendChild(bar);

            // 内容区
            var body = document.createElement('div');
            body.className = 'kz-floater-body';
            body.style.cssText = 'flex:1;overflow:hidden;display:flex;';
            if (typeof content === 'string') {
                body.innerHTML = content;
            } else if (content instanceof HTMLElement) {
                body.appendChild(content);
            }
            el.appendChild(body);

            // 默认位置
            if (opts.left !== undefined) el.style.left = opts.left + 'px';
            if (opts.top !== undefined) el.style.top = opts.top + 'px';
            if (opts.right !== undefined) el.style.right = opts.right + 'px';
            if (opts.bottom !== undefined) el.style.bottom = opts.bottom + 'px';

            document.body.appendChild(el);

            // 拖拽
            var dragging = false, ox, oy, sx, sy;
            bar.addEventListener('mousedown', function(e){
                dragging = false;
                ox = e.clientX - el.getBoundingClientRect().left;
                oy = e.clientY - el.getBoundingClientRect().top;
                sx = e.clientX; sy = e.clientY;
                el.style.transition = 'none';
                el.style.zIndex = '99999';
                // 转 left/top
                var r = el.getBoundingClientRect();
                el.style.left = r.left + 'px';
                el.style.top = r.top + 'px';
                el.style.right = 'auto';
                el.style.bottom = 'auto';
                e.preventDefault();
            });
            document.addEventListener('mousemove', function(e){
                if (!ox && ox !== 0) return;
                var dx = e.clientX - sx, dy = e.clientY - sy;
                if (!dragging && (Math.abs(dx) > 3 || Math.abs(dy) > 3)) dragging = true;
                if (!dragging) return;
                var l = e.clientX - ox, t = e.clientY - oy;
                l = Math.max(-w+40, Math.min(window.innerWidth-40, l));
                t = Math.max(0, Math.min(window.innerHeight-40, t));
                el.style.left = l + 'px';
                el.style.top = t + 'px';
            });
            document.addEventListener('mouseup', function(){
                if (dragging) {
                    el.style.transition = 'opacity 0.3s';
                }
                ox = null; oy = null;
                setTimeout(function(){ dragging = false; }, 50);
            });

            return el;
        }

        // ===== 左悬浮窗：Telemetry / 原文检索 =====
        makeFloater('kz-left', {
            title: '📡 KUNPENG TELEMETRY',
            width: 300,
            height: 460,
            left: 8,
            top: 60,
            content: '<iframe src="/left-board" style="width:100%;height:100%;border:none;"></iframe>'
        });

        // ===== 右悬浮窗：八卦辩论看板 =====
        makeFloater('kz-right', {
            title: '☯ 八卦乾坤',
            width: 300,
            height: 460,
            right: 8,
            top: 60,
            content: '<iframe src="/bagua" style="width:100%;height:100%;border:none;"></iframe>'
        });

        // ===== Google Vertex Search Widget =====
        // Trigger
        var tr = document.createElement('span');
        tr.id = 'kz-search-trigger';
        tr.style.display = 'none';
        document.body.appendChild(tr);

        // Widget 元素
        var gw = document.createElement('gen-search-widget');
        gw.setAttribute('configId', '52a37158-b391-4d50-a881-93cfd950cafc');
        gw.setAttribute('triggerId', 'kz-search-trigger');
        gw.style.display = 'none';
        document.body.appendChild(gw);

        // 🔍 悬浮搜索按钮
        var btn = document.createElement('button');
        btn.id = 'kz-search-btn';
        btn.textContent = '🔍';
        btn.title = '搜鲲鹏志知识库';
        btn.style.cssText = 'position:fixed!important;bottom:30px!important;right:30px!important;z-index:999998!important;width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,#f59e0b,#ef4444);color:#fff;font-size:24px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 16px rgba(0,0,0,0.4);border:2px solid rgba(255,255,255,0.3);cursor:pointer;transition:transform .2s,box-shadow .2s;user-select:none;';
        btn.onmouseenter = function(){ this.style.transform='scale(1.1)'; this.style.boxShadow='0 6px 24px rgba(0,0,0,0.6)'; };
        btn.onmouseleave = function(){ this.style.transform='scale(1)'; this.style.boxShadow='0 4px 16px rgba(0,0,0,0.4)'; };
        btn.onclick = function(){
            console.log('[鲲鹏志] 🔍 点击');
            var t = document.getElementById('kz-search-trigger');
            if (t) {
                t.click();
                console.log('[鲲鹏志] trigger.click()');
            }
        };
        document.body.appendChild(btn);

        // 🔍 按钮可拖拽
        (function(){
            var dragging = false, ox, oy, sx, sy;
            btn.addEventListener('mousedown', function(e){
                dragging = false; ox = null; oy = null;
                ox = e.clientX - btn.getBoundingClientRect().left;
                oy = e.clientY - btn.getBoundingClientRect().top;
                sx = e.clientX; sy = e.clientY;
            });
            document.addEventListener('mousemove', function(e){
                if (ox === null && ox === undefined) return;
                var dx = e.clientX - sx, dy = e.clientY - sy;
                if (!dragging && (Math.abs(dx) > 3 || Math.abs(dy) > 3)) {
                    dragging = true;
                }
                if (!dragging) return;
                btn.style.transition = 'none';
                btn.style.left = (e.clientX - ox) + 'px';
                btn.style.top = (e.clientY - oy) + 'px';
                btn.style.right = 'auto';
                btn.style.bottom = 'auto';
            });
            document.addEventListener('mouseup', function(){
                if (dragging) {
                    btn.style.transition = 'transform .2s,box-shadow .2s';
                }
                ox = null; oy = null;
                setTimeout(function(){ if(!dragging)return; dragging = false; }, 100);
            });
            btn.addEventListener('click', function(e){
                if (dragging) { e.stopPropagation(); return; }
            });
        })();

        // ===== 加载 Google Widget 脚本 =====
        var gs = document.createElement('script');
        gs.src = 'https://cloud.google.com/ai/gen-app-builder/client?hl=zh_CN';
        gs.async = true;
        gs.onload = function(){ console.log('[鲲鹏志] Google Widget ✅'); };
        gs.onerror = function(){ console.error('[鲲鹏志] Google Widget ❌'); };
        requestAnimationFrame(function(){ document.head.appendChild(gs); });

        console.log('[鲲鹏志] v5 注入完成 ✅');
    });
})();
