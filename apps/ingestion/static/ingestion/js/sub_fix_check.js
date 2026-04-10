document.addEventListener("DOMContentLoaded", () => {

    /* ================= STATE ================= */
    const MAX_TITLE = 64;
    const MAX_TEXTAREA_HEIGHT = 250;


    const state = {
        isProcessing: false,
        socket: null,
        taskId: null,
        modalOpenedAt: null
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

    /* ================= WS ================= */
    function connectWS() {

        if (state.socket && state.socket.readyState === WebSocket.OPEN) return;

        const protocol = window.location.protocol === "https:" ? "wss" : "ws";

        state.socket = new WebSocket(`${protocol}://${window.location.host}/ws/ingestion/`);

        state.socket.onmessage = (e) => {
            const data = JSON.parse(e.data);

            switch (data.type) {

                case "start":
                    el.progressModal.show();
                    state.modalOpenedAt = Date.now();

                    el.progressBar.style.width = "0%";
                    el.progressPercent.textContent = "0%";
                    break;

                case "progress":
                    el.progressBar.style.width = data.percent + "%";
                    el.progressPercent.textContent = data.percent + "%";
                    break;

                case "words_chunk":
                    renderWords(data.words);
                    break;

                case "done":
                    el.progressBar.style.width = "100%";
                    el.progressPercent.textContent = "100%";

                    const MIN_VISIBLE_TIME = 500; // ms

                    const elapsed = Date.now() - (state.modalOpenedAt || 0);
                    const delay = Math.max(0, MIN_VISIBLE_TIME - elapsed);

                    setTimeout(() => {
                        el.progressModal.hide();
                    }, delay);

                    el.wordsSection.style.display = "block";
                    unlockUI();
                    break;

                case "error":
                    console.error(data.message);
                    el.progressModal.hide();
                    unlockUI();
                    break;
            }
        };
    }

    /* ================= WORDS ================= */
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

    function updateWordsCount() {
        const tbody = el.wordsTable.querySelector("tbody");
        const count = tbody ? tbody.children.length : 0;
        el.wordsCount.textContent = `Слов: ${count}`;
    }

    /* ================= PROCESS ================= */
    async function startProcessing() {

        if (state.isProcessing) return;

        state.isProcessing = true;

        connectWS();
        lockUI();

        const fd = new FormData();

        if (el.file.files[0]) {
            fd.append("subtitle_file", el.file.files[0]);
        } else if (el.text.value.trim()) {
            fd.append("subtitle_text", el.text.value.trim());
        } else {
            unlockUI();
            state.isProcessing = false;
            return;
        }

        try {
            const res = await fetch(window.SUBTITLE_START_URL, {
                method: "POST",
                body: fd,
                headers: {
                    "X-CSRFToken": getCookie("csrftoken")
                }
            });

            const data = await res.json();

            if (data.status === "ok") {
                state.taskId = data.task_id;  // 🔥 КЛЮЧЕВОЕ
            } else {
                throw new Error("start failed");
            }

        } catch (e) {
            console.error(e);
            unlockUI();
            state.isProcessing = false;
        }
    }

    /* ================= SAVE ================= */
    async function saveList() {
        console.log("CLICK SAVE");
        const name = el.title.value.trim();
        if (!name) {
            alert("Введите название");
            return;
        }

        if (!state.taskId) {
            alert("Ошибка: нет task_id (обработка не завершена)");
            return;
        }

        // 🔥 1. СРАЗУ поднимаем UI + состояние
        window.startSaveToast(name, null);

        // 🔥 2. Гарантируем подключение WS (если вдруг не подключён)
        connectSaveSocket();

        const fd = new FormData();
        fd.append("subtitle_name", name);
        fd.append("task_id", state.taskId);
        fd.append("background_color", el.bgColor.value);

        if (el.bgImage.files.length) {
            fd.append("background_image", el.bgImage.files[0]);
        }

        try {
            const res = await fetch(window.SUBTITLE_SAVE_URL, {
                method: "POST",
                body: fd,
                headers: {
                    "X-CSRFToken": getCookie("csrftoken")
                }
            });

            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }

            const data = await res.json();

            if (data.status !== "ok") {
                throw new Error(data.message || "save failed");
            }

            // 🔥 3. Сохраняем реальный task_id (для восстановления)
            if (data.save_task_id) {
                localStorage.setItem("save_task_id", data.save_task_id);
            }

        } catch (e) {
            console.error("SAVE ERROR:", e);

            toastr.clear();
            toastr.error("Ошибка сохранения");

            clearSavingState();
        }
    }

    /* ================= EVENTS ================= */
    el.processBtn.onclick = startProcessing;
    el.saveBtn.onclick = saveList;

    el.file.onchange = startProcessing;

    el.wordsTable.addEventListener("click", async (e) => {
        if (!e.target.classList.contains("delete-word-btn")) return;

        const tr = e.target.closest("tr");

        const fd = new FormData();
        fd.append("word_id", tr.dataset.wordId);
        fd.append("task_id", state.taskId);

        await fetch(window.SUBTITLE_DELETE_URL, {
            method: "POST",
            body: fd,
            headers: { "X-CSRFToken": getCookie("csrftoken") }
        });

        tr.remove();
        updateWordsCount();
    });

    /* ================= PREVIEW ================= */
    el.title.addEventListener("input", () => {
        if (el.title.value.length > MAX_TITLE) {
            el.title.value = el.title.value.slice(0, MAX_TITLE);
        }
        el.previewTitle.textContent = el.title.value || "Название списка";
    });
    el.title.value = "test"
    function applyPreviewBg() {
        if (el.bgImage.files.length > 0) return;
        el.previewCard.style.backgroundImage = "";
        el.previewCard.style.backgroundColor = el.bgColor.value;
    }

    el.bgImage.addEventListener("change", function () {
        const file = this.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            el.previewCard.style.backgroundImage = `url(${e.target.result})`;
        };
        reader.readAsDataURL(file);
    });

    document.querySelectorAll('.color-swatch').forEach(btn => {
        btn.onclick = () => {
            const color = btn.dataset.color;
            if (!color) return;
            el.bgColor.value = color;
            applyPreviewBg();
        };
    });

});