const { createApp } = Vue;

createApp({
    data() {
        return {
            lists: [],
            csrftoken: this.getCookie("csrftoken"),
        };
    },
    mounted() {
        this.fetchLists();
    },
    methods: {
        getCookie(name) {
            let cookieValue = null;
            document.cookie.split(";").forEach(c => {
                c = c.trim();
                if (c.startsWith(name + "=")) {
                    cookieValue = decodeURIComponent(c.substring(name.length + 1));
                }
            });
            return cookieValue;
        },
        async fetchLists() {
            const res = await fetch("/api/user-subtitle-lists/");
            const data = await res.json();
            // добавляем поля для UI
            this.lists = data.map(list => ({
                ...list,
                is_open_menu: list.is_open_menu,
                progress_percent: list.progress_percent || 0,
                is_owner: list.owner === CURRENT_USER_ID, // передать из шаблона
                is_staff: CURRENT_USER_IS_STAFF,         // передать из шаблона
                user_authenticated: true,
                liked: list.is_liked,
                likes_count: list.likes_count || 0,
            }));
        },
        listCardStyle(list) {
            if (list.background_image) {
                return `background-image: url('${list.background_image}'); background-size: cover; background-position: center;`;
            }
            return `background-color: ${list.background_color};`;
        },
        async deleteList(list) {
            if (!confirm("Удалить список?")) return;
            const res = await fetch(`/lists/${list.id}/delete/`, {
                method: "POST",
                headers: { "X-CSRFToken": this.csrftoken },
            });
            if (res.ok) {
                this.lists = this.lists.filter(l => l.id !== list.id);
            } else alert("Ошибка при удалении");
        },
        async togglePublish(list) {
            const res = await fetch(`/lists/${list.id}/toggle-publish/`, {
                method: "POST",
                headers: { "X-CSRFToken": this.csrftoken },
            });
            const data = await res.json();
            list.is_public = data.is_public;
        },
        async updateProgress(list) {
            const res = await fetch(`/study/${list.id}/update-progress/`, {
                method: "POST",
                headers: { "X-CSRFToken": this.csrftoken },
            });
            const data = await res.json();
            list.user_quantity_learned_words = data.learned;
            list.progress_percent = data.percent;
        },
        async toggleLike(list) {
            const url = `/lists/${list.id}/toggle-like/`; // или data.url
            const res = await fetch(url, {
                method: "POST",
                headers: { "X-CSRFToken": this.csrftoken },
            });
            const data = await res.json();
            list.liked = data.liked;
            list.likes_count = data.likes_count;
        },
        async toggleMenu(list) {
            list.is_open_menu = !list.is_open_menu;
            await fetch(`/lists/${list.id}/toggle-menu/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": this.csrftoken,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ is_open_menu: list.is_open_menu }),
            });
        }
    }
}).mount("#lists-app");
