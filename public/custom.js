// 鲲鹏志 · Chainlit 自定义注入脚本

// ─── 1. 左右看板 ───────────────────────────────
function injectSidebars() {
    if (document.getElementById('left-sidebar')) return;
    
    const leftSidebar = document.createElement('div');
    leftSidebar.id = 'left-sidebar';
    leftSidebar.className = 'fixed-sidebar';
    leftSidebar.innerHTML = '<iframe src="/left-board" style="width:100%; height:100%; border:none;"></iframe>';
    document.body.appendChild(leftSidebar);

    const rightSidebar = document.createElement('div');
    rightSidebar.id = 'right-sidebar';
    rightSidebar.className = 'fixed-sidebar';
    rightSidebar.innerHTML = '<iframe src="/bagua" style="width:100%; height:100%; border:none;"></iframe>';
    document.body.appendChild(rightSidebar);
}

// ─── 2. 浮动 Q&A 小窗（白嫖 $1000 App Builder）────
function injectQAWidget() {
    console.log("鲲鹏志: Qfunction injectQAWidget()A widget 注入开始..."); {
    if (document.getElementById('qa-float-btn')) return;

    // 加载 Google Widget 脚本
    const script = document.createElement('script');
    script.src = 'https://cloud.google.com/ai/gen-app-builder/client?hl=zh_CN';
    script.async = true;
    document.head.appendChild(script);

    // 创建 widget 元素（隐藏）
    const widget = document.createElement('gen-search-widget');
    widget.setAttribute('configId', '52a37158-b391-4d50-a881-93cfd950cafc');
    widget.setAttribute('triggerId', 'qaFloatTrigger');
    widget.style.display = 'none';
    document.body.appendChild(widget);

    // 创建浮动按钮
    const btn = document.createElement('div');
    btn.id = 'qa-float-btn';
    btn.innerHTML = '🔍';
    btn.title = '搜鲲鹏志知识库';
    btn.style.cssText = `
        position: fixed;
        bottom: 100px;
        right: 20px;
        z-index: 9999;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: linear-gradient(135deg, #f59e0b, #ef4444);
        color: white;
        font-size: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.2s, box-shadow 0.2s;
        border: none;
        user-select: none;
    `;
    btn.onmouseenter = () => { btn.style.transform = 'scale(1.1)'; btn.style.boxShadow = '0 6px 20px rgba(0,0,0,0.4)'; };
    btn.onmouseleave = () => { btn.style.transform = 'scale(1)'; btn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)'; };

    // 点击时激活搜索
    btn.onclick = () => {
        const trigger = document.getElementById('qaFloatTrigger');
        if (trigger) trigger.click();
    };

    // 隐藏的 trigger 元素
    const trigger = document.createElement('span');
    trigger.id = 'qaFloatTrigger';
    trigger.style.display = 'none';
    document.body.appendChild(trigger);
    document.body.appendChild(btn);

    // 嵌入额外样式
    const style = document.createElement('style');
    style.textContent = `
        .gen-search-widget-answer {
            font-family: "Noto Sans SC", sans-serif !important;
        }
        .gen-search-widget-answer b, .gen-search-widget-answer strong {
            color: #f59e0b !important;
        }
    `;
    document.head.appendChild(style);
}

// ─── 注入 ───────────────────────────────────────
if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', () => {
        injectSidebars();
        injectQAWidget();
    });
} else {
    injectSidebars();
    injectQAWidget();
}

// 测试标记：脚本执行了就在 body 加个红点
(function(){
    const dot = document.createElement('div');
    dot.id = 'script-test-dot';
    dot.style.cssText = 'position:fixed;top:10px;left:10px;z-index:99999;width:12px;height:12px;background:red;border-radius:50%;';
    document.body.appendChild(dot);
    console.log('鲲鹏志: custom.js 已执行 ✅');
})();
