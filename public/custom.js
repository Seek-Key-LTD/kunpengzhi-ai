// 鲲鹏志 · Chainlit 左右固定看板注入脚本
function injectSidebars() {
    if (document.getElementById('left-sidebar')) return;
    
    // 创建左边侧边栏 (RAG原文/系统监控)
    const leftSidebar = document.createElement('div');
    leftSidebar.id = 'left-sidebar';
    leftSidebar.className = 'fixed-sidebar';
    leftSidebar.innerHTML = '<iframe src="/left-board" style="width:100%; height:100%; border:none;"></iframe>';
    document.body.appendChild(leftSidebar);

    // 创建右边侧边栏 (八卦流程图)
    const rightSidebar = document.createElement('div');
    rightSidebar.id = 'right-sidebar';
    rightSidebar.className = 'fixed-sidebar';
    rightSidebar.innerHTML = '<iframe src="/bagua" style="width:100%; height:100%; border:none;"></iframe>';
    document.body.appendChild(rightSidebar);
}

// 轮询检测以确保注入
if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', injectSidebars);
} else {
    injectSidebars();
}
