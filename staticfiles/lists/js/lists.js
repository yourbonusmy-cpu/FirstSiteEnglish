// Получение CSRF токена из cookie
function getCookie(name) {
    let cookieValue = null;
    document.cookie.split(';').forEach(c => {
        c = c.trim();
        if (c.startsWith(name + '=')) {
            cookieValue = decodeURIComponent(c.substring(name.length + 1));
        }
    });
    return cookieValue;
}

document.addEventListener("DOMContentLoaded", () => {
    const csrftoken = getCookie("csrftoken");

    // Обработчик удаления
    document.querySelectorAll(".delete-list").forEach(btn => {
        btn.addEventListener("click", async function () {
            if (!confirm("Удалить список?")) return;

            const listId = this.dataset.listId;

            try {
                const res = await fetch(`/list/${listId}/delete/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrftoken,
                    },
                });

                if (res.ok) {
                    // Плавное исчезновение карточки
                    const col = this.closest(".col-md-6");
                    col.style.transition = "opacity 0.3s ease, transform 0.3s ease";
                    col.style.opacity = "0";
                    col.style.transform = "scale(0.95)";
                    setTimeout(() => col.remove(), 300);
                } else {
                    const text = await res.text();
                    console.error("Ошибка удаления:", text);
                    alert("Ошибка при удалении");
                }
            } catch(e) {
                console.error(e);
                alert("Ошибка при удалении");
            }
        });
    });
    const switches = document.querySelectorAll(".publish-switch");

    switches.forEach(sw => {
        sw.addEventListener("change", function () {
            const listId = this.dataset.listId;

            fetch(`/lists/${listId}/toggle-publish/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                }
            })
            .then(res => {
                if (!res.ok) {
                    this.checked = !this.checked;
                    throw new Error("Permission denied");
                }
                return res.json();
            })
            .then(data => {
                this.checked = data.is_public;
            })
            .catch(() => {
                this.checked = !this.checked;
            });
        });
    });

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(
        `${protocol}://${window.location.host}/ws/likes/`
    );

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        const listId = data.list_id;
        const likesCount = data.likes_count;

        const btn = document.querySelector(
            `.like-btn[data-list-id="${listId}"]`
        );

        if (btn) {
            const countEl = btn.parentElement.querySelector(".likes-count");
            countEl.textContent = likesCount;
        }
    };

    socket.onclose = function () {
        console.warn("WebSocket closed");
    };


    document.querySelectorAll(".like-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            const listId = this.dataset.listId;
            const icon = this.querySelector("i");
            const countEl = this.parentElement.querySelector(".likes-count");

            fetch(`/lists/${listId}/toggle-like/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.liked) {
                    icon.classList.remove("bi-heart");
                    icon.classList.add("bi-heart-fill", "text-danger");
                } else {
                    icon.classList.remove("bi-heart-fill", "text-danger");
                    icon.classList.add("bi-heart");
                }

                countEl.textContent = data.likes_count;
            });
        });
    });
});
