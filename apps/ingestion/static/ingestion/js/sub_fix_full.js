document.addEventListener('DOMContentLoaded', function () {

    /* ============================================================
       DOM
    ============================================================ */

    const fileInput = document.getElementById('subtitle-file');
    const textArea = document.getElementById('subtitle-text');
    const processBtn = document.getElementById('process-text-btn');
    const titleInput = document.getElementById('subtitle-name');

    const wordsWrapper = document.getElementById("words-table-wrapper");
    const wordsTable = document.getElementById("words-table");
    const wordsSection = document.getElementById("words-section");

    const saveBtnTop = document.getElementById('save-btn-top');
    const saveBtnBottom = document.getElementById('save-btn-bottom');
    const clearBtnTop = document.getElementById('clear-btn-top');
    const clearBtnBottom = document.getElementById('clear-btn-bottom');

    const wordsCountTop = document.getElementById('words-count-top');
    const wordsCountBottom = document.getElementById('words-count-bottom');

    const backgroundColorInput = document.getElementById('background-color-input');
    const backgroundImageInput = document.getElementById('background-image');
    const resetImageBtn = document.getElementById('reset-image');

    const directPicker = document.getElementById('direct-color-picker');

    /* ===== Preview DOM ===== */
    const previewCard = document.querySelector('.list-card');
    const previewTitle = document.querySelector('.card-title-span');
    const previewLearnedCount = document.querySelector('.learned-count');

    /* ============================================================
       GLOBAL STATE (КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ)
    ============================================================ */

    window.SUBTITLE_WORDS_CACHE = {};
    window.SUBTITLE_WORDS_ORDER = [];
    window.SUBTITLE_WORDS_PAGE = 1;
    window.SUBTITLE_HAS_NEXT = true;
    window.SUBTITLE_LOADING = false;
    window.SUBTITLE_TOTAL_COUNT = 0;
    let CURRENT_PAGE = 1;
    let LOADING = false;
    let TOTAL_COUNT = 0;

    /* ============================================================
       UTILS
    ============================================================ */

    function getCookie(name) {
        return document.cookie
            .split("; ")
            .find(row => row.startsWith(name + "="))
            ?.split("=")[1];
    }
    /* ============================================================
       INPUT SOURCE LOGIC
    ============================================================ */

    function handleInputChange() {
        const hasFile = fileInput?.files.length > 0;
        const hasText = textArea.value.trim().length > 0;

        processBtn.classList.toggle('d-none', !(hasText && !hasFile));

        textArea.style.height = '1px';
        textArea.style.height = textArea.scrollHeight + 'px';
    }

    /* ============================================================
       WORD COUNT (ИСПРАВЛЕНО)
    ============================================================ */

    function updateCounter() {
        wordsCountTop.textContent = `Слов: ${TOTAL_COUNT}`;
        wordsCountBottom.textContent = `Слов: ${TOTAL_COUNT}`;
        previewLearnedCount.textContent = `${TOTAL_COUNT} слов`;
    }

    /* ============================================================
       CLEAR
    ============================================================ */

    function clearAll() {
        fileInput.value = "";
        textArea.value = "";
        titleInput.value = "";
        wordsTable.innerHTML = "";
        wordsSection.style.display = "none";

        previewTitle.textContent = "Название списка";
        previewLearnedCount.textContent = "0 слов";

        previewCard.style.backgroundImage = "";
        previewCard.style.backgroundColor = backgroundColorInput.value;

        window.SUBTITLE_WORDS_CACHE = {};
        window.SUBTITLE_WORDS_ORDER = [];
        window.SUBTITLE_WORDS_PAGE = 1;
        window.SUBTITLE_HAS_NEXT = true;
        window.SUBTITLE_TOTAL_COUNT = 0;

        handleInputChange();
        updateCounter();
    }

    /* ============================================================
       AUTO PREVIEW
    ============================================================ */

    async function autoPreview() {
        const formData = new FormData();
        if (fileInput.files[0]) {
            formData.append("subtitle_file", fileInput.files[0]);
        } else if (textArea.value.trim()) {
            formData.append("subtitle_text", textArea.value.trim());
        } else {
            return;
        }

        const res = await fetch(window.SUBTITLE_PREVIEW_URL, {
            method: "POST",
            body: formData,
            headers: { "X-CSRFToken": getCookie("csrftoken") },
        });

        const data = await res.json();
        if (data.error) {
            alert(data.error);
            return;
        }

        TOTAL_COUNT = data.total_count;
        CURRENT_PAGE = 1;
        wordsTable.innerHTML = "";
        wordsSection.style.display = "block";

        updateCounter();
        await loadNextPage();
    }

    /* ============================================================
       SERVER-SIDE PAGINATION (ИСПРАВЛЕНО)
    ============================================================ */

    async function loadNextPage() {
        if (LOADING) return;
        LOADING = true;

        const res = await fetch(
            `${window.SUBTITLE_PAGE_URL}?page=${CURRENT_PAGE}`,
            { credentials: "same-origin" }
        );

        const data = await res.json();
        if (!data.words.length) {
            LOADING = false;
            return;
        }

        renderWords(data.words);
        CURRENT_PAGE += 1;
        LOADING = false;
    }

    /* ============================================================
       TABLE RENDER
    ============================================================ */

    function ensureTable() {
        if (wordsTable.querySelector("table")) return;

        wordsTable.innerHTML = `
            <table class="table table-striped table-bordered align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>#</th>
                        <th>Слово</th>
                        <th>Транскрипция</th>
                        <th>Часть речи</th>
                        <th>Перевод</th>
                        <th>Частота</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        `;
    }

    function renderWords(words) {
        ensureTable();
        const tbody = wordsTable.querySelector("tbody");

        const html = words.map((w, i) => `
            <tr data-temp-id="${w.temp_id}">
                <td>${tbody.children.length + i + 1}</td>
                <td>${w.name}</td>
                <td>${w.transcription || ""}</td>
                <td>
                    <select class="form-select pos-select">
                        ${w.pos_list.map(p =>
                            `<option ${p === w.selected_pos ? "selected" : ""}>${p}</option>`
                        ).join("")}
                    </select>
                </td>
                <td>
                    <select class="form-select translation-select">
                        ${(w.translations_for_pos[w.selected_pos] || []).map(t =>
                            `<option ${t === w.selected_translation ? "selected" : ""}>${t}</option>`
                        ).join("")}
                    </select>
                </td>
                <td>${w.frequency}</td>
                <td>
                    <button class="btn btn-sm btn-outline-danger delete-word">✖</button>
                </td>
            </tr>
        `).join("");

        tbody.insertAdjacentHTML("beforeend", html);
        attachDeleteHandlers();
    }

    wordsWrapper.addEventListener('scroll', () => {
        if (wordsWrapper.scrollTop + wordsWrapper.clientHeight >= wordsWrapper.scrollHeight - 50) {
            loadNextPage();
        }
    });

    /* ============================================================
       TABLE EVENTS
    ============================================================ */

    function attachTableEvents() {

        document.querySelectorAll(".delete-word").forEach(btn => {
            if (btn.dataset.bound) return;
            btn.dataset.bound = "1";

            btn.addEventListener("click", function () {
                const tr = this.closest("tr");
                const temp_id = tr.dataset.tempId;

                delete window.SUBTITLE_WORDS_CACHE[temp_id];
                window.SUBTITLE_WORDS_ORDER =
                    window.SUBTITLE_WORDS_ORDER.filter(id => id !== temp_id);

                tr.remove();
                window.SUBTITLE_TOTAL_COUNT -= 1;
                updateCounter();
            });
        });

        document.querySelectorAll('.pos-select').forEach(select => {
            if (select.dataset.bound) return;
            select.dataset.bound = "1";

            select.addEventListener('change', function () {
                const tr = this.closest("tr");
                const temp_id = tr.dataset.tempId;
                const w = window.SUBTITLE_WORDS_CACHE[temp_id];

                w.selected_pos = this.value;

                const translations = w.translations_for_pos[this.value] || [];
                const trSelect = tr.querySelector('.translation-select');

                trSelect.innerHTML = translations.map(t =>
                    `<option value="${t}">${t}</option>`
                ).join('');
            });
        });

        document.querySelectorAll('.translation-select').forEach(select => {
            if (select.dataset.bound) return;
            select.dataset.bound = "1";

            select.addEventListener('change', function () {
                const tr = this.closest("tr");
                const temp_id = tr.dataset.tempId;
                window.SUBTITLE_WORDS_CACHE[temp_id].selected_translation = this.value;
            });
        });
    }

    /* ============================================================
       SAVE (КРИТИЧЕСКИ ИСПРАВЛЕНО)
    ============================================================ */

    async function saveList() {

        if (!window.SUBTITLE_WORDS_ORDER.length) {
            alert("Нет слов для сохранения");
            return;
        }

        const formData = new FormData();
        formData.append("subtitle_name", titleInput.value.trim());
        formData.append("background_color", backgroundColorInput.value);

        if (backgroundImageInput.files[0]) {
            formData.append("background_image", backgroundImageInput.files[0]);
        }

        window.SUBTITLE_WORDS_ORDER.forEach(temp_id => {
            const w = window.SUBTITLE_WORDS_CACHE[temp_id];
            formData.append("words", JSON.stringify({
                name: w.name,
                transcription: w.transcription,
                selected_pos: w.selected_pos,
                selected_translation: w.selected_translation,
                frequency: w.frequency
            }));
        });

        try {
            const res = await fetch(window.SUBTITLE_SAVE_URL, {
                method: "POST",
                body: formData,
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });

            const data = await res.json();

            if (data.status === "ok") {
                window.location.href = data.redirect_url;
            } else {
                alert("Ошибка при сохранении списка");
            }

        } catch (e) {
            alert("Ошибка при сохранении");
            console.error(e);
        }
    }

    /* ============================================================
       PREVIEW BACKGROUND
    ============================================================ */

    function applyPreviewBackground() {
        if (backgroundImageInput.files.length > 0) return;
        previewCard.style.backgroundImage = "";
        previewCard.style.backgroundColor = backgroundColorInput.value;
    }

    directPicker.addEventListener('input', () => {
        backgroundColorInput.value = directPicker.value;
        applyPreviewBackground();
    });

    resetImageBtn.addEventListener('click', () => {
        backgroundImageInput.value = '';
        applyPreviewBackground();
    });

    /* ============================================================
       EVENTS
    ============================================================ */

    fileInput?.addEventListener('change', () => {
        textArea.value = '';
        handleInputChange();
        autoPreview();
    });

    textArea?.addEventListener('input', handleInputChange);
    processBtn?.addEventListener('click', autoPreview);

    saveBtnTop?.addEventListener('click', saveList);
    saveBtnBottom?.addEventListener('click', saveList);

    clearBtnTop?.addEventListener('click', clearAll);
    clearBtnBottom?.addEventListener('click', clearAll);

    titleInput?.addEventListener('input', function () {
        previewTitle.textContent = this.value.trim() || "Название списка";
    });

    /* INIT */
    handleInputChange();
    applyPreviewBackground();
    updateCounter();
});