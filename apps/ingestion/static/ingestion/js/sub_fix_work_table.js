document.addEventListener("DOMContentLoaded", () => {

    const fileInput = document.getElementById("subtitle-file");
    const textArea = document.getElementById("subtitle-text");
    const processBtn = document.getElementById("process-text-btn");

    const wordsWrapper = document.getElementById("words-table-wrapper");
    const wordsTable = document.getElementById("words-table");
    const wordsSection = document.getElementById("words-section");

    const wordsCountTop = document.getElementById("words-count-top");
    const wordsCountBottom = document.getElementById("words-count-bottom");
    const previewLearnedCount = document.querySelector(".learned-count");

    let CURRENT_PAGE = 1;
    let LOADING = false;
    let TOTAL_COUNT = 0;

    function getCookie(name) {
        return document.cookie
            .split("; ")
            .find(row => row.startsWith(name + "="))
            ?.split("=")[1];
    }

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

    function updateCounter() {
        wordsCountTop.textContent = `Слов: ${TOTAL_COUNT}`;
        wordsCountBottom.textContent = `Слов: ${TOTAL_COUNT}`;
        previewLearnedCount.textContent = `${TOTAL_COUNT} слов`;
    }

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

    function attachDeleteHandlers() {
        document.querySelectorAll(".delete-word").forEach(btn => {
            if (btn.dataset.bound) return;
            btn.dataset.bound = "1";

            btn.addEventListener("click", async () => {
                const tr = btn.closest("tr");
                const tempId = tr.dataset.tempId;

                await fetch(window.SUBTITLE_DELETE_WORD_URL, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    body: `temp_id=${tempId}`,
                });

                tr.remove();
                TOTAL_COUNT -= 1;
                updateCounter();
            });
        });
    }

    wordsWrapper.addEventListener("scroll", () => {
        if (
            wordsWrapper.scrollTop + wordsWrapper.clientHeight >=
            wordsWrapper.scrollHeight - 50
        ) {
            loadNextPage();
        }
    });

    fileInput.addEventListener("change", autoPreview);
    processBtn.addEventListener("click", autoPreview);
});