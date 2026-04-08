function getCookie(name) {
    let cookieValue = null;
    document.cookie.split(";").forEach(c => {
        c = c.trim();
        if (c.startsWith(name + "=")) {
            cookieValue = decodeURIComponent(c.substring(name.length + 1));
        }
    });
    return cookieValue;
}

document.addEventListener("DOMContentLoaded", () => {
    const csrftoken = getCookie("csrftoken");

    // ===== Удаление списка =====
    document.querySelectorAll(".delete-list").forEach(btn => {
        btn.addEventListener("click", async () => {
            if (!confirm("Удалить список?")) return;

            const listId = btn.dataset.listId;
            const col = btn.closest(".col");

            try {
                const res = await fetch(`/lists/${listId}/delete/`, {
                    method: "POST",
                    headers: { "X-CSRFToken": csrftoken },
                });

                if (res.ok) {
                    col.style.transition = "0.3s";
                    col.style.opacity = "0";
                    col.style.transform = "scale(0.95)";
                    setTimeout(() => col.remove(), 300);
                } else {
                    alert("Ошибка при удалении");
                }
            } catch {
                alert("Ошибка сети");
            }
        });
    });

    // ===== Публикация =====
    document.querySelectorAll(".publish-switch").forEach(sw => {
        sw.addEventListener("change", () => {
            const listId = sw.dataset.listId;

            fetch(`/lists/${listId}/toggle-publish/`, {
                method: "POST",
                headers: { "X-CSRFToken": csrftoken },
            })
            .then(res => res.json())
            .then(data => sw.checked = data.is_public)
            .catch(() => sw.checked = !sw.checked);
        });
    });

    // ===== Обновление прогресса =====
    document.querySelectorAll(".progress-ring-wrapper").forEach(el => {
        el.addEventListener("click", async () => {
            const listId = el.dataset.listId;

            const res = await fetch(`/study/${listId}/update-progress/`, {
                method: "POST",
                headers: { "X-CSRFToken": csrftoken },
            });
            const data = await res.json();

            el.style.setProperty("--percent", data.percent);
            el.querySelector(".progress-ring").classList.remove("empty");
            el.querySelector(".progress-ring-label").textContent = `${data.percent}%`;

            const counter = document.querySelector(`.learned-counter[data-list-id="${listId}"]`);
            if (counter) {
                let learnedSpan = counter.querySelector(".learned-count");
                counter.innerHTML = `<span class="learned-count">${data.learned}</span> из ${data.total} <i class="bi bi-check-lg"></i>`;

            }
        });
    });

    document.addEventListener('DOMContentLoaded', function () {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl)
        })
    })

    // ===== Лайки =====
    document.querySelectorAll(".like-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            const url = btn.dataset.url;
            const icon = btn.querySelector("i");
            const countEl = btn.parentElement.querySelector(".likes-count");

            fetch(url, {
                method: "POST",
                headers: { "X-CSRFToken": csrftoken },
            })
            .then(res => res.json())
            .then(data => {
                if (data.liked) {
                    icon.classList.remove("bi-heart-fill", "text-secondary");
                    icon.classList.add("bi-heart-fill", "text-danger");
                } else {
                    icon.classList.remove("bi-heart-fill", "text-danger");
                    icon.classList.add("bi-heart-fill", "text-secondary");
                }
                countEl.textContent = data.likes_count;
            });
        });
    });

});
