document.addEventListener('DOMContentLoaded', function () {

    /* ============================================================
       DOM ELEMENTS
    ============================================================ */
    const fileInput = document.getElementById('subtitle-file');
    const textArea = document.getElementById('subtitle-text');
    const processBtn = document.getElementById('process-text-btn');
    const titleInput = document.getElementById('subtitle-name');

    const wordsTableWrapper = document.getElementById("words-table-wrapper");
    const wordsTable = document.getElementById("words-table");
    const wordsSection = document.getElementById("words-section");

    const saveBtnTop = document.getElementById('save-btn-top');
    const saveBtnBottom = document.getElementById('save-btn-bottom');
    const clearBtnTop = document.getElementById('clear-btn-top');
    const clearBtnBottom = document.getElementById('clear-btn-bottom');

    const wordsCountTop = document.getElementById('words-count-top');
    const wordsCountBottom = document.getElementById('words-count-bottom');
    const previewLearnedCount = document.querySelector('.learned-count');

    const backgroundColorInput = document.getElementById('background-color-input');
    const backgroundImageInput = document.getElementById('background-image');
    const previewCard = document.querySelector('.list-card');
    const previewTitle = document.querySelector('.card-title-span');
    const resetImageBtn = document.getElementById('reset-image');

    let currentPage = 1;
    const pageSize = 50;
    let loading = false;
    previewTitle.textContent = "Название списка";

    const form = document.getElementById("subtitle-form");

    form.addEventListener("submit", function (e) {
        e.preventDefault();  // ⛔ запрещаем стандартную отправку
    });

    /* ============================================================
       HELPERS
    ============================================================ */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie) {
            document.cookie.split(';').forEach(cookie => {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            });
        }
        return cookieValue;
    }

    function updateWordsCountFromTotal() {
        const count = window.TOTAL_WORDS || 0;
        wordsCountTop.textContent = `Слов: ${count}`;
        wordsCountBottom.textContent = `Слов: ${count}`;
        previewLearnedCount.textContent = `${count} слов`;
    }

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

        currentPage = 1;
        loading = false;

        handleInputChange();
        updateWordsCountFromTotal();
    }

    function applyPreviewBackground() {
        if (backgroundImageInput.files.length > 0) return;
        previewCard.style.backgroundImage = "";
        previewCard.style.backgroundColor = backgroundColorInput.value;
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

        const MAX_HEIGHT = 250; // макс. высота в px
        textArea.style.height = 'auto'; // сброс, чтобы уменьшалась при удалении
        const newHeight = Math.min(textArea.scrollHeight, MAX_HEIGHT);
        textArea.style.height = newHeight + 'px';
        textArea.style.overflowY = textArea.scrollHeight > MAX_HEIGHT ? 'auto' : 'hidden';
    }

    const colorCol = document.getElementById("color-col");

    function updateImageState() {
        const hasImage = backgroundImageInput.files.length > 0;

        // Показываем/скрываем кнопку reset
        resetImageBtn.classList.toggle("d-none", !hasImage);

        // Скрываем/показываем выбор цвета
        colorCol.style.display = hasImage ? "none" : "";
    }

    /* ============================================================
       RENDER WORDS
    ============================================================ */
    function renderWordsTable(words, append=false) {
        let table = wordsTable.querySelector('table');
        if (!table) {
            table = document.createElement('table');
            table.className = "table table-striped table-hover table-bordered align-middle";
            table.innerHTML = `
                <thead class="table-dark">
                    <tr>
                        <th>#</th>
                        <th>Слово</th>
                        <th>Транскрипция</th>
                        <th>Часть речи</th>
                        <th>Перевод</th>
                        <th>Частотность</th>
                        <th></th>
                    </tr>
                </thead>
            `;
            const tbody = document.createElement('tbody');
            table.appendChild(tbody);
            wordsTable.innerHTML = '';
            wordsTable.appendChild(table);
        }

        const tbody = table.querySelector('tbody');
        const startIndex = append ? tbody.children.length : 0;

        words.forEach((w, idx) => {
            const tr = document.createElement('tr');
            tr.classList.add('word-row');
            tr.dataset.index = startIndex + idx;
            tr.dataset.tempId = w.temp_id;

            tr.innerHTML = `
                <td>${parseInt(tr.dataset.index)+1}</td>
                <td>${w.name}</td>
                <td>${w.transcription || ''}</td>
                <td>
                    <select class="form-select pos-select">
                        ${w.pos_list.map(pos => `<option value="${pos}" ${pos===w.selected_pos?'selected':''}>${pos}</option>`).join('')}
                    </select>
                </td>
                <td>
                    <select class="form-select translation-select">
                        ${(w.translations_for_pos[w.selected_pos] || []).map(tr => `<option value="${tr}" ${tr===w.selected_translation?'selected':''}>${tr}</option>`).join('')}
                    </select>
                </td>
                <td>${w.frequency || '-'}</td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-danger delete-word">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        attachTableEvents();
        wordsSection.style.display = 'block';
        updateWordsCountFromTotal();
    }

    function attachTableEvents() {
        document.querySelectorAll(".delete-word").forEach(btn => {
            btn.onclick = async () => {
                const tr = btn.closest("tr");
                const tempId = tr.dataset.tempId;

                try {
                    const formData = new FormData();
                    formData.append("temp_id", tempId);

                    const res = await fetch(window.SUBTITLE_DELETE_URL, {
                        method: "POST",
                        body: formData,
                        headers: {'X-CSRFToken': getCookie('csrftoken')}
                    });

                    const data = await res.json();

                    if (data.status === "ok") {
                        tr.remove();
                        window.TOTAL_WORDS = data.total_words;
                        updateWordsCountFromTotal();

                        document.querySelectorAll("#words-table tbody tr").forEach((row, idx) => {
                            row.dataset.index = idx;
                            row.children[0].textContent = idx + 1;
                        });

                        if (!data.total_words) wordsSection.style.display = "none";
                    }
                } catch (e) { console.error(e); }
            };
        });
    }

    /* ============================================================
       AUTO PREVIEW + SERVER CACHE
    ============================================================ */
    async function autoPreview() {
        if (!fileInput.files[0] && !textArea.value.trim()) return;

        const formData = new FormData();
        if (fileInput.files[0]) formData.append("subtitle_file", fileInput.files[0]);
        else formData.append("subtitle_text", textArea.value.trim());

        try {
            const res = await fetch(window.SUBTITLE_PREVIEW_URL, {
                method: "POST",
                body: formData,
                credentials: "same-origin",
                headers: {'X-CSRFToken': getCookie('csrftoken')}
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const data = await res.json();
            if (data.error) return alert("Ошибка предпросмотра: " + data.error);

            if (data.subtitle_name) {
                if (titleInput.value.length < 1){
                    titleInput.value = data.subtitle_name;
                    previewTitle.textContent = data.subtitle_name;
                }
            }

            currentPage = 1;
            window.TOTAL_WORDS = data.total_words;
            wordsTable.innerHTML = '';
            renderWordsTable(data.words, false);

        } catch (e) {
            alert("Ошибка предпросмотра");
            console.error(e);
        }
    }

    /* ============================================================
       INFINITE SCROLL
    ============================================================ */
    wordsTableWrapper.addEventListener('scroll', async () => {
        if (loading) return;
        if (wordsTableWrapper.scrollTop + wordsTableWrapper.clientHeight >= wordsTableWrapper.scrollHeight - 10) {
            const loadedWords = document.querySelectorAll("#words-table tbody tr").length;
            if (loadedWords >= window.TOTAL_WORDS) return;

            loading = true;
            currentPage += 1;

            try {
                const res = await fetch(`${window.SUBTITLE_PAGE_URL}?page=${currentPage}&page_size=${pageSize}`, {
                    method: "GET",
                    credentials: "same-origin"
                });

                if (!res.ok) throw new Error("Ошибка загрузки страницы");

                const data = await res.json();
                renderWordsTable(data.words, true);

            } catch (e) { console.error(e); }
            loading = false;
        }
    });

    /* ============================================================
       SAVE LIST
    ============================================================ */
    async function saveList() {
        const formDataSave = new FormData();
        formDataSave.append("subtitle_name", titleInput.value.trim());
        formDataSave.append("background_color", backgroundColorInput.value);
        if (backgroundImageInput.files.length > 0) formDataSave.append("background_image", backgroundImageInput.files[0]);

        document.querySelectorAll("#words-table tbody tr").forEach(tr => {
            formDataSave.append("temp_ids", tr.dataset.tempId);
        });

        try {
            const res = await fetch(window.SUBTITLE_SAVE_URL, {
                method: "POST",
                body: formDataSave,
                headers: {'X-CSRFToken': getCookie('csrftoken')}
            });

            const data = await res.json();
            if (data.status === "ok") window.location.href = data.redirect_url;
            else alert(data.message || "Ошибка при сохранении списка");
        } catch (e) { console.error(e); alert("Ошибка при сохранении списка"); }
    }

    /* ============================================================
       EVENTS
    ============================================================ */
    fileInput.onchange = () => { textArea.value=''; handleInputChange(); autoPreview(); };
    textArea.oninput = handleInputChange;
    processBtn.onclick = autoPreview;

    saveBtnTop.onclick = saveList;
    saveBtnBottom.onclick = saveList;
    clearBtnTop.onclick = clearAll;
    clearBtnBottom.onclick = clearAll;

    titleInput.addEventListener('input', () => {
        if (titleInput.value.length > 64) {
            titleInput.value = titleInput.value.slice(0, MAX_LENGTH);
        }
        previewTitle.textContent = titleInput.value.trim() || "Название списка";
    });

    resetImageBtn?.addEventListener("click", () => {
        backgroundImageInput.value = "";
        previewCard.style.backgroundImage = "";
        applyPreviewBackground();
        updateImageState();
    });

    document.querySelectorAll('.color-swatch').forEach(btn => {
        btn.onclick = () => {
            const color = btn.dataset.color;
            if (!color) return;
            backgroundColorInput.value = color;
            document.querySelectorAll('.color-swatch').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            applyPreviewBackground();
        };
    });

    backgroundImageInput?.addEventListener("change", function () {
        const file = this.files[0];
        if (!file) {
            applyPreviewBackground();
            updateImageState();
            return;
        }
        const reader = new FileReader();
        reader.onload = function (e) {
            previewCard.style.backgroundImage = `url(${e.target.result})`;
            previewCard.style.backgroundSize = "cover";
            previewCard.style.backgroundPosition = "center";
        };
        reader.readAsDataURL(file);
        updateImageState();
    });

    /* INIT */
    handleInputChange();
    applyPreviewBackground();
    updateImageState();

});
