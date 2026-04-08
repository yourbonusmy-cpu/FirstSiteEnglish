document.addEventListener("DOMContentLoaded", function () {

    const container = document.getElementById("word-container");
    const loadingEl = document.getElementById("loading");
    const searchInput = document.getElementById("search-input");

    if (!container) return;

    let page = 1;
    let loading = false;
    let hasNext = true;
    let currentQuery = "";


    /* ==========================
       LOAD WORDS
    ========================== */
    async function loadWords(reset = false) {

        if (loading) return;
        loading = true;

        if (reset) {
            page = 1;
            container.innerHTML = "";
            hasNext = true;
        }

        if (!hasNext) return;

        if (loadingEl) loadingEl.style.display = "block";

        const params = new URLSearchParams();
        params.set("page", page);

        if (currentQuery) {
            params.set("q", currentQuery);
        }

        const res = await fetch(`/study/known-words/ajax/?${params.toString()}`);
        const data = await res.json();

        container.insertAdjacentHTML("beforeend", data.html);

        hasNext = data.has_next;
        page++;

        loading = false;
        if (loadingEl) loadingEl.style.display = "none";
    }


    /* ==========================
       SEARCH (debounce)
    ========================== */
    let debounceTimer;

    searchInput.addEventListener("input", function () {

        clearTimeout(debounceTimer);

        debounceTimer = setTimeout(() => {
            currentQuery = searchInput.value.trim();
            loadWords(true);   // reset = true
        }, 400);

    });


    /* ==========================
       INFINITE SCROLL
    ========================== */
    window.addEventListener("scroll", function () {

        if (!hasNext || loading) return;

        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200) {
            loadWords();
        }

    });


    /* ==========================
       TOGGLE
    ========================== */
    document.addEventListener("click", async function (e) {
        const btn = e.target.closest(".known-toggle");
        if (!btn) return;

        const wordCard = btn.closest(".card");
        const wordId = btn.dataset.wordId;
        const mode = btn.dataset.mode; // "learned"
        const csrftoken = getCookie("csrftoken");

        const formData = new FormData();
        formData.append("word_id", wordId);
        formData.append("mode", mode);

        const res = await fetch("/study/word/update-state/", {
            method: "POST",
            headers: { "X-CSRFToken": csrftoken },
            body: formData,
        });

        const data = await res.json();

        if (data.status === "ok") {
            if (data.state.is_learned) {
                wordCard.classList.add("border", "border-3", "border-success");
            } else {
                wordCard.classList.remove("border", "border-3", "border-success");
            }
        } else {
            console.error("Ошибка обновления слова:", data.message);
        }
    });


    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

});
