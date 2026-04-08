document.addEventListener("DOMContentLoaded", () => {

    /* ================= STATE ================= */
    const MAX_TITLE = 64;
    const MAX_TEXTAREA_HEIGHT = 250;

    const state = {
        isProcessing: false,
        controller: null,
        taskId: null,
        page: 1,
        hasNext: true,
        loading: false,
        showModalTimer: null
    };

    /* ================= DOM ================= */
    const el = {
        file: document.getElementById("subtitle-file"),
        text: document.getElementById("subtitle-text"),
        processBtn: document.getElementById("process-text-btn"),
        title: document.getElementById("subtitle-name"),

        wordsWrapper: document.getElementById("words-table-wrapper"),
        wordsTable: document.getElementById("words-table"),
        wordsSection: document.getElementById("words-section"),
        wordsCount: document.getElementById("words-count-top"),
        saveBtn: document.getElementById("save-btn-top"),

        progressModal: new bootstrap.Modal(document.getElementById("progressModal"), {
            backdrop: 'static',
            keyboard: false
        }),
        progressBar: document.getElementById("progress-bar"),
        progressPercent: document.getElementById("progress-percent"),
        progressText: document.getElementById("progress-text"),
        cancelBtn: document.getElementById("cancel-processing"),

        bgColor: document.getElementById('background-color-input'),
        bgImage: document.getElementById('background-image'),
        previewCard: document.querySelector('.list-card'),
        previewTitle: document.querySelector('.card-title-span'),
        resetImage: document.getElementById('reset-image'),
        colorPicker: document.getElementById('color-picker'),
        colorCol: document.getElementById("color-col")
    };

    /* ================= HELPERS ================= */
    const getCookie = (name) =>
        document.cookie.split("; ").find(r => r.startsWith(name + "="))?.split("=")[1];

    const sleep = (ms) => new Promise(r => setTimeout(r, ms));

    async function request(url, { method = "GET", body = null, signal } = {}) {
        const res = await fetch(url, {
            method,
            body,
            signal,
            headers: { "X-CSRFToken": getCookie("csrftoken") }
        });
        if (!res.ok) throw new Error("Request failed");
        return res.json();
    }

    function lockUI() {
        el.processBtn.disabled = true;
        el.file.disabled = true;
        el.text.disabled = true;
    }

    function unlockUI() {
        el.processBtn.disabled = false;
        el.file.disabled = false;
        el.text.disabled = false;
    }

    /* ================= PREVIEW ================= */
    function applyPreviewBg() {
        if (el.bgImage.files.length > 0) return;
        el.previewCard.style.backgroundImage = "";
        el.previewCard.style.backgroundColor = el.bgColor.value;
    }

    function updateImageState() {
        const hasImage = el.bgImage.files.length > 0;
        el.resetImage.classList.toggle("d-none", !hasImage);
        el.colorCol.style.display = hasImage ? "none" : "";
    }

    function updateTextareaHeight() {
        el.text.style.height = "auto";
        const h = Math.min(el.text.scrollHeight, MAX_TEXTAREA_HEIGHT);
        el.text.style.height = h + "px";
        el.text.style.overflowY = el.text.scrollHeight > MAX_TEXTAREA_HEIGHT ? "auto" : "hidden";
    }

    /* ================= INPUT ================= */
    function handleInputChange() {
        const hasFile = el.file.files.length > 0;
        const hasText = el.text.value.trim().length > 0;

        el.processBtn.classList.toggle('d-none', !(hasText && !hasFile));
        updateTextareaHeight();

        const fileCol = document.getElementById('file-col');
        const textCol = document.getElementById('text-col');

        if (hasText) {
            fileCol.style.display = 'none';
            textCol.classList.replace('col-md-6', 'col-12');
        } else if (hasFile) {
            textCol.style.display = 'none';
            fileCol.classList.replace('col-md-6', 'col-12');
        } else {
            fileCol.style.display = '';
            textCol.style.display = '';
            fileCol.classList.replace('col-12', 'col-md-6');
            textCol.classList.replace('col-12', 'col-md-6');
        }
    }

    /* ================= WORDS ================= */
    function updateWordsCount() {
        const tbody = el.wordsTable.querySelector("tbody");
        const displayed = tbody ? tbody.children.length : 0;
        const total = window.TOTAL_WORDS || 0;

        el.wordsCount.textContent = `Слов: ${displayed}/${total}`;

        document.querySelectorAll(".learned-count").forEach(span => {
            span.textContent = `${displayed}/${total}`;
        });
    }

    function ensureTable() {
        if (el.wordsTable.querySelector("table")) return;

        el.wordsTable.innerHTML = `
            <table class="table table-striped table-bordered">
                <thead>
                    <tr><th>#</th><th>Слово</th><th>Частота</th><th></th></tr>
                </thead>
                <tbody></tbody>
            </table>`;
    }

    function renderWords(words) {
        ensureTable();
        const tbody = el.wordsTable.querySelector("tbody");

        words.forEach(w => {
            tbody.insertAdjacentHTML("beforeend", `
                <tr data-word-id="${w.id}">
                    <td>${tbody.children.length + 1}</td>
                    <td>${w.name}</td>
                    <td>${w.frequency}</td>
                    <td><button class="btn btn-sm btn-danger delete-word-btn">X</button></td>
                </tr>
            `);
        });

        updateWordsCount();
    }

    async function loadNextPage() {
        if (state.loading || !state.hasNext) return;
        state.loading = true;

        const data = await request(`${window.SUBTITLE_PAGE_URL}?task_id=${state.taskId}&page=${state.page}`);

        if (!data.words.length) {
            state.hasNext = false;
            state.loading = false;
            return;
        }

        renderWords(data.words);
        window.TOTAL_WORDS = data.total;

        state.page++;
        state.hasNext = data.has_next;
        state.loading = false;
    }

    /* ================= PROCESSING ================= */
    async function startProcessing() {
        if (state.isProcessing) return;

        state.controller?.abort();
        state.controller = new AbortController();
        state.isProcessing = true;

        const fd = new FormData();
        if (el.file.files[0]) fd.append("subtitle_file", el.file.files[0]);
        else if (el.text.value.trim()) fd.append("subtitle_text", el.text.value.trim());
        else return;

        lockUI();

        try {
            const { task_id } = await request(window.SUBTITLE_START_URL, {
                method: "POST",
                body: fd,
                signal: state.controller.signal
            });

            state.taskId = task_id;

            state.showModalTimer = setTimeout(() => el.progressModal.show(), 300);

            await pollProgress();

        } catch {
            state.isProcessing = false;
            unlockUI();
        }
    }

    async function pollProgress() {
        const { progress = 0 } = await request(`${window.SUBTITLE_PROGRESS_URL}?task_id=${state.taskId}`);

        el.progressBar.style.width = progress + "%";
        el.progressPercent.textContent = progress + "%";

        if (progress < 100) {
            await sleep(500);
            return pollProgress();
        }

        await finalizeProcessing();
    }

    async function finalizeProcessing() {
        el.wordsTable.innerHTML = "";
        state.page = 1;
        state.hasNext = true;

        for (let i = 0; i < 5; i++) {
            await loadNextPage();
            if (el.wordsTable.querySelector("tbody")?.children.length) break;
            await sleep(200);
        }

        if (state.showModalTimer) {
            clearTimeout(state.showModalTimer);
            state.showModalTimer = null;
        }

        setTimeout(() => el.progressModal.hide(), 300);

        el.wordsSection.style.display = "block";
        state.isProcessing = false;
        unlockUI();

        updateWordsCount();
    }

    /* ================= SAVE ================= */
    async function saveList() {
        if (!state.taskId) return alert("Ошибка: task_id отсутствует");

        // ✅ Получаем все слова из Redis по правильной логике
        const data = await request(`${window.SUBTITLE_PAGE_URL}?task_id=${state.taskId}&page=1`);
        const totalWords = data.total;
        if (!totalWords) return alert("Нет слов для сохранения");

        const name = el.title.value.trim();
        if (!name) return alert("Введите название");

        const fd = new FormData();
        fd.append("subtitle_name", name);
        fd.append("task_id", state.taskId);
        fd.append("background_color", el.bgColor.value);

        if (el.bgImage.files.length) {
            fd.append("background_image", el.bgImage.files[0]);
        }

        const res = await request(window.SUBTITLE_SAVE_URL, {
            method: "POST",
            body: fd
        });

        if (res.status === "ok") {
            window.startSaveToast(name, res.save_task_id);  // 🔥 ВАЖНО
        } else {
            alert("Ошибка сохранения");
        }
    }

    /* ================= EVENTS ================= */
    el.text.oninput = handleInputChange;

    el.file.onchange = () => {
        const file = el.file.files[0];
        if (!file) return;

        if (!el.title.value.trim()) {
            let name = file.name.replace(/\.[^/.]+$/, "");
            if (name.length > MAX_TITLE) name = name.slice(0, MAX_TITLE - 3) + "...";
            el.title.value = name;
            el.previewTitle.textContent = name;
        }

        startProcessing();
    };

    el.processBtn.onclick = startProcessing;
    el.saveBtn.onclick = saveList;

    el.cancelBtn.onclick = () => {
        state.controller?.abort();
        state.isProcessing = false;
        unlockUI();
        el.progressModal.hide();
    };

    el.wordsWrapper?.addEventListener("scroll", () => {
        if (el.wordsWrapper.scrollTop + el.wordsWrapper.clientHeight >= el.wordsWrapper.scrollHeight - 50) {
            loadNextPage();
        }
    });

    el.wordsTable.addEventListener("click", async (e) => {
        if (!e.target.classList.contains("delete-word-btn")) return;

        const tr = e.target.closest("tr");

        const fd = new FormData();
        fd.append("task_id", state.taskId);
        fd.append("word_id", tr.dataset.wordId);

        const data = await request(window.SUBTITLE_DELETE_URL, {
            method: "POST",
            body: fd
        });

        if (data.status === "ok") {
            tr.remove();
            updateWordsCount();
        }
    });

    /* ================= COLORS ================= */
    el.colorPicker?.addEventListener("input", () => {
        el.bgColor.value = el.colorPicker.value;
        applyPreviewBg();
    });

    el.resetImage?.addEventListener("click", () => {
        el.bgImage.value = "";
        el.previewCard.style.backgroundImage = "";
        applyPreviewBg();
        updateImageState();
    });

    document.querySelectorAll('.color-swatch').forEach(btn => {
        btn.onclick = () => {
            const color = btn.dataset.color;
            if (!color) return;
            el.bgColor.value = color;
            document.querySelectorAll('.color-swatch').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            applyPreviewBg();
        };
    });

    el.title.addEventListener("input", () => {
        if (el.title.value.length > MAX_TITLE) {
            el.title.value = el.title.value.slice(0, MAX_TITLE);
        }
        el.previewTitle.textContent = el.title.value.trim() || "Название списка";
    });

    el.bgImage?.addEventListener("change", function () {
        const file = this.files[0];
        if (!file) {
            applyPreviewBg();
            updateImageState();
            return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            el.previewCard.style.backgroundImage = `url(${e.target.result})`;
            el.previewCard.style.backgroundSize = "cover";
            el.previewCard.style.backgroundPosition = "center";
        };
        reader.readAsDataURL(file);
        updateImageState();
    });

    /* ================= INIT ================= */
    handleInputChange();
    updateImageState();

    function initDefaultColor() {
        const color = "#ffffff";
        el.bgColor.value = color;
        el.colorPicker.value = color;
        applyPreviewBg();

        const btn = document.querySelector(`.color-swatch[data-color="${color}"]`);
        if (btn) btn.classList.add("active");
    }

    initDefaultColor();
    el.previewTitle.textContent = "Название списка";

});