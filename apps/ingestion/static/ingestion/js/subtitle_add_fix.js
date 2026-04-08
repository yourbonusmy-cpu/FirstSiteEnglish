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
    const showPickerBtn = document.getElementById('show-direct-picker');

    /* ===== Preview DOM ===== */
    const previewCard = document.querySelector('.list-card');
    const previewTitle = document.querySelector('.card-title-span');
    const previewLearnedCount = document.querySelector('.learned-count');

    /* ============================================================
       UTILS
    ============================================================ */

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie) {
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

    /* ============================================================
       INPUT SOURCE LOGIC
    ============================================================ */

    function handleInputChange() {
        const fileCol = document.getElementById('file-col');
        const textCol = document.getElementById('text-col');

        const hasFile = fileInput.files.length > 0;
        const hasText = textArea.value.trim().length > 0;

        processBtn.classList.toggle('d-none', !(hasText && !hasFile));

        if (hasText) {
            fileCol.style.display = 'none';
            textCol.classList.remove('col-md-6');
            textCol.classList.add('col-12');
        } else if (hasFile) {
            textCol.style.display = 'none';
            fileCol.classList.remove('col-md-6');
            fileCol.classList.add('col-12');
        } else {
            fileCol.style.display = '';
            textCol.style.display = '';
            fileCol.classList.remove('col-12');
            fileCol.classList.add('col-md-6');
            textCol.classList.remove('col-12');
            textCol.classList.add('col-md-6');
        }

        textArea.style.height = '1px';
        textArea.style.height = textArea.scrollHeight + 'px';
    }

    /* ============================================================
       WORD COUNT
    ============================================================ */

    function updateWordsCount() {
        const count = window.SUBTITLE_WORDS_ORDER?.length || 0;
        wordsCountTop.textContent = `Слов: ${count}`;
        wordsCountBottom.textContent = `Слов: ${count}`;
        previewLearnedCount.textContent = `${count} слов`;
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
        window.SUBTITLE_WORDS_PAGE = 0;
        handleInputChange();
        updateWordsCount();
    }

    /* ============================================================
       AUTO PREVIEW
    ============================================================ */

    async function autoPreview() {
        if (!fileInput.files[0] && !textArea.value.trim()) return;

        const formData = new FormData();

        if (fileInput.files[0]) {
            formData.append("subtitle_file", fileInput.files[0]);
        } else {
            formData.append("subtitle_text", textArea.value.trim());
        }

        try {
            const res = await fetch(window.SUBTITLE_PREVIEW_URL, {
                method: "POST",
                body: formData,
                credentials: "same-origin",
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const data = await res.json();
            if (data.error) {
                alert("Ошибка предпросмотра data: " + data.error);
                return;
            }

            if (data.subtitle_name) {
                titleInput.value = data.subtitle_name;
                previewTitle.textContent = data.subtitle_name;
            }
            window.SUBTITLE_WORDS_CACHE = {};
            window.SUBTITLE_WORDS_ORDER = [];
            window.SUBTITLE_WORDS_PAGE = 1;

            wordsTable.innerHTML = "";
            wordsSection.style.display = "block";

            await loadNextPageFromServer();
            updateWordsCount();

        } catch (e) {
            alert("Ошибка предпросмотра");
            console.error(e);
        }
    }

    /* ============================================================
       TABLE RENDER (server-side pagination)
    ============================================================ */

    async function loadNextPageFromServer() {
        const res = await fetch(`${window.SUBTITLE_PAGE_URL}?page=${window.SUBTITLE_WORDS_PAGE}`, {
            credentials: "same-origin",
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        if (!res.ok) return;

        const data = await res.json();
        if (!data.words.length) return;

        data.words.forEach(w => {
            window.SUBTITLE_WORDS_CACHE[w.temp_id] = w;
            window.SUBTITLE_WORDS_ORDER.push(w.temp_id);
        });

        renderWords(data.words);
        window.SUBTITLE_WORDS_PAGE += 1;

        updateWordsCountFromServer(data.total_count);
    }
    function updateWordsCountFromServer(total) {
        wordsCountTop.textContent = `Слов: ${total}`;
        wordsCountBottom.textContent = `Слов: ${total}`;
        previewLearnedCount.textContent = `${total} слов`;
    }

    function renderWords(words) {
        const html = words.map((w, idx) => `
            <tr data-temp-id="${w.temp_id}">
                <td>${w.name}</td>
                <td>${w.transcription || ''}</td>
                <td>
                    <select class="form-select pos-select">
                        ${w.pos_list.map(p =>
                            `<option ${p === w.selected_pos ? 'selected' : ''}>${p}</option>`
                        ).join('')}
                    </select>
                </td>
                <td>
                    <select class="form-select translation-select">
                        ${(w.translations_for_pos[w.selected_pos] || []).map(t =>
                            `<option ${t === w.selected_translation ? 'selected' : ''}>${t}</option>`
                        ).join('')}
                    </select>
                </td>
                <td>${w.frequency}</td>
                <td>
                    <button class="btn btn-sm btn-outline-danger delete-word">🗑</button>
                </td>
            </tr>
        `).join('');

        ensureTable();
        document.querySelector("#words-table tbody")
            .insertAdjacentHTML("beforeend", html);

        attachTableEvents();
    }

    wordsWrapper.addEventListener('scroll', () => {
        const wrapper = wordsWrapper;
        if (wrapper.scrollTop + wrapper.clientHeight >= wrapper.scrollHeight - 50) {
            loadNextPage();
        }
    });

    /* ============================================================
       ATTACH EVENTS
    ============================================================ */

    function attachTableEvents() {
        document.querySelectorAll(".delete-word").forEach(btn => {
            if (btn.dataset.listenerAttached) return;
            btn.dataset.listenerAttached = true;

            btn.addEventListener("click", function () {
                const tr = this.closest("tr");
                const temp_id = tr.dataset.tempId;

                delete window.SUBTITLE_WORDS_CACHE[temp_id];
                const index = window.SUBTITLE_WORDS_ORDER.indexOf(temp_id);
                if (index > -1) window.SUBTITLE_WORDS_ORDER.splice(index, 1);

                tr.remove();
                updateWordsCount();
            });
        });

        document.querySelectorAll('.pos-select').forEach(select => {
            if (select.dataset.listenerAttached) return;
            select.dataset.listenerAttached = true;

            select.addEventListener('change', function() {
                const tr = this.closest("tr");
                const temp_id = tr.dataset.tempId;
                const w = window.SUBTITLE_WORDS_CACHE[temp_id];
                const trSelect = tr.querySelector('.translation-select');
                const translations = w.translations_for_pos[this.value] || [];
                trSelect.innerHTML = translations.map(t =>
                    `<option value="${t}">${t}</option>`
                ).join('');
                w.selected_pos = this.value;
            });
        });

        document.querySelectorAll('.translation-select').forEach(select => {
            if (select.dataset.listenerAttached) return;
            select.dataset.listenerAttached = true;

            select.addEventListener('change', function() {
                const tr = this.closest("tr");
                const temp_id = tr.dataset.tempId;
                window.SUBTITLE_WORDS_CACHE[temp_id].selected_translation = this.value;
            });
        });
    }

    /* ============================================================
       SAVE
    ============================================================ */

    async function saveList() {
        const formDataSave = new FormData();
        formDataSave.append("subtitle_name", titleInput.value.trim());
        formDataSave.append("background_color", backgroundColorInput.value);

        if (backgroundImageInput.files.length > 0) {
            formDataSave.append("background_image", backgroundImageInput.files[0]);
        }

        const words = window.SUBTITLE_WORDS_ORDER.map(temp_id => {
            const w = window.SUBTITLE_WORDS_CACHE[temp_id];
            return {
                name: w.name,
                transcription: w.transcription,
                selected_pos: w.selected_pos,
                selected_translation: w.selected_translation,
                frequency: w.frequency
            };
        });

        words.forEach(w => formDataSave.append("words", JSON.stringify(w)));

        try {
            const res = await fetch(window.SUBTITLE_SAVE_URL, {
                method: "POST",
                body: formDataSave,
                headers: {'X-CSRFToken': getCookie('csrftoken')}
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
       COLOR PICKER + PREVIEW SYNC
    ============================================================ */

    function applyPreviewBackground() {
        if (backgroundImageInput.files.length > 0) return;
        previewCard.style.backgroundImage = "";
        previewCard.style.backgroundColor = backgroundColorInput.value;
    }

    document.querySelectorAll('.color-swatch').forEach(btn => {
        btn.addEventListener('click', function () {
            const color = this.dataset.color;
            if (!color) return;

            backgroundColorInput.value = color;

            document.querySelectorAll('.color-swatch').forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            applyPreviewBackground();
        });
    });

    resetImageBtn.addEventListener('click', () => {
        previewCard.style.backgroundImage = '';
        if (backgroundImageInput) backgroundImageInput.value = '';
        previewCard.style.backgroundColor = backgroundColorInput.value;
    });

    directPicker.addEventListener('input', () => {
        backgroundColorInput.value = directPicker.value;
        applyPreviewBackground();
    });

    backgroundImageInput?.addEventListener("change", function () {
        const file = this.files[0];
        if (!file) {
            applyPreviewBackground();
            return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            previewCard.style.backgroundImage = `url(${e.target.result})`;
            previewCard.style.backgroundSize = "cover";
            previewCard.style.backgroundPosition = "center";
        };
        reader.readAsDataURL(file);
    });

    /* ============================================================
       EVENTS
    ============================================================ */

    fileInput?.addEventListener('change', function () {
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
    updateWordsCount();
});
