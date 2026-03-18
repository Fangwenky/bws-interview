// 博物社面试管理系统 - 通用JavaScript函数

// 显示消息提示
function showMessage(msg, type = 'info') {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = msg;
    div.style.position = 'fixed';
    div.style.top = '20px';
    div.style.right = '20px';
    div.style.zIndex = '9999';
    div.style.minWidth = '200px';
    document.body.appendChild(div);

    setTimeout(() => {
        div.remove();
    }, 3000);
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN');
}

// 格式化时间
function formatTime(timeStr) {
    if (!timeStr) return '-';
    return timeStr;
}

// 检查登录状态
async function checkLogin() {
    try {
        const response = await fetch('/api/stats');
        if (response.status === 401) {
            window.location.href = '/login';
            return false;
        }
        return true;
    } catch (error) {
        window.location.href = '/login';
        return false;
    }
}

// 获取URL参数
function getUrlParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 确认对话框
function confirmAction(message) {
    return confirm(message);
}

// 加载中显示
function showLoading(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = '<div class="empty-state"><p>加载中...</p></div>';
    }
}
