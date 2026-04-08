document.addEventListener("DOMContentLoaded", () => {
    const toggleThemeBtn = document.getElementById("toggleTheme");
    if (!toggleThemeBtn) return;

    function setTheme(theme) {
        document.body.dataset.theme = theme;
        localStorage.setItem("theme", theme);
    }

    toggleThemeBtn.addEventListener("click", () => {
        const current = document.body.dataset.theme === "dark" ? "light" : "dark";
        setTheme(current);
    });

    // При загрузке страницы восстанавливаем тему
    const savedTheme = localStorage.getItem("theme") || "light";
    setTheme(savedTheme);
});
