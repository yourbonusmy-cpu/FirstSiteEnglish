document.addEventListener("DOMContentLoaded", () => {

    let currentPage = 1;
    let hasNext = true;
    let loading = false;

    const container = document.getElementById("words-container");
    const trigger = document.getElementById("load-trigger");

    const searchInput = document.getElementById("word-search");
    const hideKnown = document.getElementById("filter-hide-known");
    const onlyKnown = document.getElementById("filter-only-known");
    const downloadBtn = document.getElementById("download-words"); // ← кнопка

    const SCROLL_KEY = `word-list-scroll-${LIST_ID}`;
    const PAGE_KEY = `word-list-page-${LIST_ID}`;
    const FILTER_KEY = `word-list-filters-${LIST_ID}`;

    /* ===============================
       ИНИЦИАЛИЗАЦИЯ КАРТОЧЕК
    ================================ */
    function reinitializeWordCards() {
        document.querySelectorAll(".word-card").forEach(card => {
            if (card.dataset.initialized) return;
            card.dataset.initialized = "1";

            const partSelect = card.querySelector(".part-select");
            const translationSelect = card.querySelector(".translation-select");
            const translationsBlocks = card.querySelectorAll(".translations-data");

            function updateTranslations(partId) {
                translationSelect.innerHTML = "";

                const block = Array.from(translationsBlocks)
                    .find(b => b.dataset.partId === partId);

                if (!block) return;

                block.querySelectorAll("span").forEach(span => {
                    const opt = document.createElement("option");
                    opt.textContent = span.textContent.trim();
                    if (span.dataset.isMain === "1") opt.selected = true;
                    translationSelect.appendChild(opt);
                });
            }

            if (partSelect && partSelect.value) updateTranslations(partSelect.value);

            partSelect.addEventListener("change", () => {
                updateTranslations(partSelect.value);
            });
        });
    }

    reinitializeWordCards();

    /* ===============================
       BUILD QUERY
    ================================ */
    function buildQuery(page = currentPage) {
        const params = new URLSearchParams();

        if (searchInput.value.trim()) params.append("search", searchInput.value.trim());
        if (hideKnown.checked) params.append("hide_known", "1");
        if (onlyKnown.checked) params.append("only_known", "1");
        params.append("page", page);

        return params.toString();
    }

    /* ===============================
       LOAD WORDS
    ================================ */
    async function loadWords(reset = false, pageToLoad = null) {
        if (loading) return;
        if (!hasNext && !reset && !pageToLoad) return;

        loading = true;
        trigger.style.display = "block";

        if (reset) {
            currentPage = 1;
            hasNext = true;
            container.innerHTML = "";
        }

        if (pageToLoad) currentPage = pageToLoad;

        const response = await fetch(
            `${window.location.pathname}?${buildQuery(currentPage)}`,
            { headers: { "X-Requested-With": "XMLHttpRequest" } }
        );

        const data = await response.json();

        container.insertAdjacentHTML("beforeend", data.html);

        hasNext = data.has_next;
        loading = false;

        reinitializeWordCards();
        updateURL();

        if (!hasNext) trigger.style.display = "none";

        // сохраняем страницу и фильтры
        sessionStorage.setItem(PAGE_KEY, currentPage);
        sessionStorage.setItem(FILTER_KEY, JSON.stringify({
            search: searchInput.value,
            hideKnown: hideKnown.checked,
            onlyKnown: onlyKnown.checked
        }));
    }

    function updateURL() {
        history.replaceState(null, "", `?${buildQuery()}`);
    }

    /* ===============================
       INTERSECTION OBSERVER
    ================================ */
    const observer = new IntersectionObserver(entries => {
        if (entries[0].isIntersecting && hasNext && !loading) {
            currentPage++;
            loadWords();
        }
    }, { rootMargin: "200px" });

    observer.observe(trigger);

    /* ===============================
       FILTER HANDLER
    ================================ */
    let debounce;
    function handleFilters() {
        clearTimeout(debounce);
        debounce = setTimeout(() => {
            loadWords(true); // reset = true
        }, 400);
    }

    searchInput.addEventListener("input", handleFilters);
    hideKnown.addEventListener("change", handleFilters);
    onlyKnown.addEventListener("change", handleFilters);

    /* ===============================
       SAVE SCROLL
    ================================ */
    window.addEventListener("scroll", () => {
        sessionStorage.setItem(SCROLL_KEY, window.scrollY);
    });

    /* ===============================
       RESTORE FILTERS + PAGE + SCROLL
    ================================ */
    (async () => {
        const savedFilters = sessionStorage.getItem(FILTER_KEY);
        const savedPage = sessionStorage.getItem(PAGE_KEY);
        const savedScroll = sessionStorage.getItem(SCROLL_KEY);

        // восстановим фильтры
        if (savedFilters) {
            const f = JSON.parse(savedFilters);
            searchInput.value = f.search || "";
            hideKnown.checked = f.hideKnown || false;
            onlyKnown.checked = f.onlyKnown || false;
        }

        // очистим контейнер перед восстановлением
        container.innerHTML = "";

        // восстановим страницы до текущей
        if (savedPage) {
            const pages = parseInt(savedPage);
            for (let i = 1; i <= pages; i++) {
                // указываем reset=false, чтобы не обнулять container внутри loadWords
                await loadWords(false, i);
            }
        } else {
            // если страниц не было сохранено, загрузим первую
            await loadWords(true, 1);
        }

        // восстановим скролл после загрузки DOM
        if (savedScroll) {
            window.scrollTo(0, parseInt(savedScroll));
        }
    })();

    downloadBtn.addEventListener("click", async () => {
        // если есть следующие страницы, подгружаем их все
        while (hasNext && !loading) {
            currentPage++;
            await loadWords();
        }

        // после полной загрузки собираем все ID
        const ids = [];
        document.querySelectorAll(".word-card").forEach(card => {
            const id = card.dataset.wordId;
            if (id) ids.push(id);
        });

        if (!ids.length) {
            alert("Нет слов для экспорта");
            return;
        }

        const url = `/lists/${LIST_ID}/download/?ids=${ids.join(",")}`;
        window.location.href = url;
    });

});