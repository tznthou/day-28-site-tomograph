/**
 * Site Tomograph - 主題切換
 * E1 深淵版 (Dark) / E3 淺色版 (Light)
 */

(function() {
    const STORAGE_KEY = 'site-tomograph-theme';
    const toggleBtn = document.getElementById('theme-toggle');

    if (!toggleBtn) return;

    // 取得當前主題
    function getTheme() {
        return document.documentElement.getAttribute('data-theme') || 'dark';
    }

    // 設定主題
    function setTheme(theme) {
        if (theme === 'light') {
            document.documentElement.setAttribute('data-theme', 'light');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        localStorage.setItem(STORAGE_KEY, theme);

        // 更新 3D 圖主題
        updateGraphTheme();
    }

    // 切換主題
    function toggleTheme() {
        const current = getTheme();
        const next = current === 'light' ? 'dark' : 'light';
        setTheme(next);
    }

    // 更新 3D 圖主題
    function updateGraphTheme() {
        if (window.app && window.app.graph) {
            window.app.graph.updateTheme();
        }
    }

    // 綁定事件
    toggleBtn.addEventListener('click', toggleTheme);

    // 監聽系統主題變化（可選）
    if (window.matchMedia) {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
        mediaQuery.addEventListener('change', function(e) {
            // 只有在沒有手動設定過的情況下才跟隨系統
            if (!localStorage.getItem(STORAGE_KEY)) {
                setTheme(e.matches ? 'light' : 'dark');
            }
        });
    }
})();
