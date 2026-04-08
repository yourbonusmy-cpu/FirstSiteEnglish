// -----------------------------
// Переключение темы
// -----------------------------
const themeToggleBtn = document.getElementById('themeToggleBtn');

// Применяем тему на body и navbar
function applyTheme(theme) {
    // Body
    document.body.classList.remove('light-theme', 'dark-theme');
    document.body.classList.add(theme + '-theme');

    // Navbar
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        navbar.classList.remove('light-theme', 'dark-theme');
        navbar.classList.add(theme + '-theme');
    }
}

// Сохраняем тему в localStorage
function saveTheme(theme) {
    localStorage.setItem('theme', theme);
}

// Читаем тему при загрузке
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
}

if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
        saveTheme(newTheme);
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    loadTheme();
});