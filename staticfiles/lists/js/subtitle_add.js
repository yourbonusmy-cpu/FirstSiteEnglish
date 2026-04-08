function handleInputChange() {
    const fileInput  = document.getElementById('subtitle-file');
    const textArea   = document.getElementById('subtitle-text');
    const fileCol    = document.getElementById('file-col');
    const textCol    = document.getElementById('text-col');
    const processBtn = document.getElementById('process-text-btn');

    if (!fileInput || !textArea) return;

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

function updateWordsCount() {
    const count = document.querySelectorAll('.word-row').length;
    document.getElementById('words-count-top').textContent = `Слов: ${count}`;
    document.getElementById('words-count-bottom').textContent = `Слов: ${count}`;
}

function clearAll() {
    document.getElementById("subtitle-file").value = "";
    document.getElementById("subtitle-text").value = "";
    document.getElementById("subtitle-name").value = "";
    document.getElementById("words-table").innerHTML = "";
    document.getElementById("words-section").style.display = "none";
    handleInputChange();
    updateWordsCount();
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function autoPreview() {
    const fileInput = document.getElementById("subtitle-file");
    const textInput = document.getElementById("subtitle-text");
    const csrftoken = getCookie('csrftoken');

    if (!fileInput || !textInput) return;

    if (!fileInput.files[0] && !textInput.value.trim()) return;

    const formData = new FormData();
    if (fileInput.files[0]) {
        formData.append("subtitle_file", fileInput.files[0]);
    } else {
        formData.append("subtitle_text", textInput.value.trim());
    }

    try {
        const res = await fetch("{% url 'subtitle_preview' %}", {
            method: "POST",
            body: formData,
            headers: { 'X-CSRFToken': csrftoken }
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();

        if (data.error) {
            alert("Ошибка предпросмотра: " + data.error);
            return;
        }

        if (data.subtitle_name) {
            document.getElementById("subtitle-name").value = data.subtitle_name;
        }

        const tableDiv = document.getElementById("words-table");
        tableDiv.innerHTML = `
            <table class="table table-striped table-hover table-bordered align-middle">
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
                <tbody>
                    ${data.words.map((w, idx) => `
                        <tr data-index="${idx}" class="word-row">
                            <td>${idx+1}</td>
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
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        document.getElementById("words-section").style.display = "block";
        updateWordsCount();

        document.querySelectorAll(".delete-word").forEach(btn => {
            btn.addEventListener("click", function () {
                const row = this.closest("tr");
                row.remove();
                updateWordsCount();
                const rowsLeft = document.querySelectorAll("#words-table tbody tr");
                if (rowsLeft.length === 0) {
                    document.getElementById("words-section").style.display = "none";
                    document.getElementById("subtitle-name").value = "";
                    document.getElementById("subtitle-file").value = "";
                    document.getElementById("subtitle-text").value = "";
                }
            });
        });

        document.querySelectorAll('.pos-select').forEach((select, idx) => {
            select.addEventListener('change', function() {
                const trSelect = document.querySelectorAll('.translation-select')[idx];
                const translations = data.words[idx].translations_for_pos[this.value] || [];
                trSelect.innerHTML = translations.map(t => `<option value="${t}">${t}</option>`).join('');
            });
        });

        document.getElementById("clear-btn-top").onclick = clearAll;
        document.getElementById("clear-btn-bottom").onclick = clearAll;

    } catch(e) {
        console.error("Ошибка предпросмотра:", e);
        alert("Не удалось сделать предпросмотр\n" + (e.message || ""));
    }
}

// ──────────────────────────────────────────────
// Сохранение (вынесено наружу, работает всегда)
// ──────────────────────────────────────────────
async function saveList() {
    const rows = document.querySelectorAll("#words-table tbody tr");
    if (rows.length === 0) {
        alert("Нет слов для сохранения");
        return;
    }

    const words = [];
    rows.forEach((row) => {
        const cols = row.children;
        words.push({
            name: cols[1].innerText,
            transcription: cols[2].innerText,
            selected_pos: cols[3].children[0].value,
            selected_translation: cols[4].children[0].value,
            frequency: parseInt(cols[5].innerText)
        });
    });

    const formDataSave = new FormData();
    formDataSave.append("subtitle_name", document.getElementById("subtitle-name").value.trim());

    formDataSave.append(
        "background_color",
        document.getElementById("background-color-input").value
    );

    const bgImageInput = document.getElementById("background-image");

    if (bgImageInput && bgImageInput.files.length > 0) {
        formDataSave.append(
            "background_image",
            bgImageInput.files[0]
        );
    }

    words.forEach(w => formDataSave.append("words", JSON.stringify(w)));

    const csrftoken = getCookie('csrftoken');

    try {
        const res = await fetch("{% url 'subtitle_save' %}", {
            method: "POST",
            body: formDataSave,
            headers: {'X-CSRFToken': csrftoken}
        });

        const dataSave = await res.json();

        if (dataSave.status === "ok") {
            window.location.href = dataSave.redirect_url;
        } else {
            alert("Ошибка при сохранении списка: " + (dataSave.message || "неизвестная ошибка"));
        }
    } catch (err) {
        console.error("Ошибка сохранения:", err);
        alert("Не удалось отправить данные\n" + (err.message || "проверьте консоль"));
    }
}

// ──────────────────────────────────────────────
// Инициализация — всё привязываем здесь
// ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
    console.log("Скрипт загружен и DOM готов");

    const fileInput = document.getElementById('subtitle-file');
    const textArea = document.getElementById('subtitle-text');
    const processBtn = document.getElementById('process-text-btn');

    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            console.log("Файл выбран:", e.target.files.length > 0 ? e.target.files[0].name : "нет файла");
            if (e.target.files.length > 0) {
                document.getElementById('subtitle-text').value = '';
                handleInputChange();
                autoPreview();
            }
        });
    }

    if (textArea) {
        textArea.addEventListener('input', handleInputChange);
    }

    if (processBtn) {
        processBtn.addEventListener('click', autoPreview);
    }

    document.getElementById('save-btn-top').addEventListener('click', saveList);
    document.getElementById('save-btn-bottom').addEventListener('click', saveList);
    document.getElementById('clear-btn-top').addEventListener('click', clearAll);
    document.getElementById('clear-btn-bottom').addEventListener('click', clearAll);

    document.querySelectorAll('.color-swatch').forEach(btn => {
    btn.addEventListener('click', function () {
        const color = this.dataset.color;
        if (!color) return;

        // записываем цвет в hidden input
        document.getElementById('background-color-input').value = color;

        // визуально отмечаем выбранный цвет
        document.querySelectorAll('.color-swatch').forEach(b => {
            b.classList.remove('active');
        });
        this.classList.add('active');
    });
});

    handleInputChange();
});

    // ──────────────────────────────────────────────
// Выбор цвета фона
// ──────────────────────────────────────────────
(function initColorPicker() {
    const swatches = document.querySelectorAll('.color-swatch[data-color]');
    const hiddenInput = document.getElementById('background-color-input');
    const customBtn = document.getElementById('custom-color-btn');
    const customInput = document.getElementById('custom-color-input');

    function setActive(el, color) {
        swatches.forEach(s => s.classList.remove('active'));
        customBtn.classList.remove('active');
        el.classList.add('active');
        hiddenInput.value = color;
    }

    swatches.forEach(btn => {
        btn.addEventListener('click', () => {
            setActive(btn, btn.dataset.color);
        });
    });

    customBtn.addEventListener('click', () => {
        customInput.click();
    });

    customInput.addEventListener('input', () => {
        const color = customInput.value;
        customBtn.style.background = color;
        setActive(customBtn, color);
    });

    // активируем белый по умолчанию
    const defaultBtn = document.querySelector('.color-swatch[data-color="#ffffff"]');
    if (defaultBtn) {
        defaultBtn.classList.add('active');
    }
})();
