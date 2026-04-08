// ========================================
// GLOBAL SAVE PROGRESS MANAGER (ADVANCED)
// ========================================

toastr.options = {
    positionClass: "toast-bottom-right",
    timeOut: 0,
    extendedTimeOut: 0,
    closeButton: false,
    escapeHtml: false,
};

let socket = null;
let reconnectTimeout = null;
let isConnecting = false;

// ================================
// Helpers
// ================================

function getCookie(name) {
    return document.cookie.split("; ")
        .find(row => row.startsWith(name + "="))
        ?.split("=")[1];
}

function setSavingState(name) {
    localStorage.setItem("save_in_progress", "1");
    localStorage.setItem("save_list_name", name);
    updateHeaderIndicator(true);
}

function clearSavingState() {
    localStorage.removeItem("save_in_progress");
    localStorage.removeItem("save_list_name");
    updateHeaderIndicator(false);
}

// ================================
// Header indicator
// ================================

function updateHeaderIndicator(active) {
    const el = document.getElementById("global-save-indicator");
    if (!el) return;

    if (active) {
        el.classList.remove("d-none");
        el.classList.add("d-flex");
    } else {
        el.classList.add("d-none");
        el.classList.remove("d-flex");
    }
}

// ================================
// WebSocket
// ================================

function connectSaveSocket() {

    if (socket && socket.readyState === WebSocket.OPEN) return;
    if (isConnecting) return;

    isConnecting = true;

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";

    socket = new WebSocket(`${protocol}://${window.location.host}/ws/save-progress/`);

    socket.onopen = () => {
        isConnecting = false;
        console.log("Save WS connected");
    };

    socket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        handleSaveEvent(data);
    };

    socket.onerror = () => {
        console.warn("WS error");
    };

    socket.onclose = () => {
        console.warn("WS closed, reconnecting...");
        socket = null;

        if (localStorage.getItem("save_in_progress")) {
            reconnectTimeout = setTimeout(connectSaveSocket, 2000);
        }
    };
}

// ================================
// Events
// ================================

function handleSaveEvent(data) {

    if (data.type === "start") {
        setSavingState(data.name);
        showToast(data.name);
    }

    if (data.type === "progress") {
        if (!document.getElementById("save-progress")) {
            const name = localStorage.getItem("save_list_name") || "Сохранение...";
            showToast(name);
        }
        updateProgress(data.percent);
    }

    if (data.type === "done") {

        updateProgress(100);

        toastr.clear();
        toastr.success("Список успешно сохранён");

        clearSavingState();
    }

    if (data.type === "error") {

        toastr.clear();
        toastr.error("Ошибка сохранения: " + (data.message || ""));

        clearSavingState();
    }
}

// ================================
// Toast UI
// ================================

function showToast(name) {

    if (document.getElementById("save-progress")) return;

    toastr.info(`
        <div>
            <strong>Сохранение списка</strong><br>
            <small>${name}</small>
            <div class="progress mt-2">
                <div id="save-progress"
                     class="progress-bar progress-bar-striped progress-bar-animated"
                     style="width:0%">
                </div>
            </div>
            <button class="btn btn-sm btn-outline-light mt-2"
                    onclick="cancelSave()">
                Отменить
            </button>
        </div>
    `);
}

function updateProgress(percent) {
    const bar = document.getElementById("save-progress");
    if (bar) bar.style.width = percent + "%";
}

// ================================
// Cancel
// ================================

window.cancelSave = function () {
    const taskId = localStorage.getItem("save_task_id");
    if (!taskId) return;

    fetch("/ingestion/subtitle/save-cancel/", {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        body: new URLSearchParams({ task_id: taskId })
    });

    toastr.warning("Сохранение отменено");
    clearSavingState();
};

// ================================
// Public API
// ================================

window.startSaveToast = function (name, taskId) {
    if (localStorage.getItem("save_in_progress")) return;

    if (!taskId) {
        console.warn("No taskId passed to startSaveToast");
        return;
    }

    localStorage.setItem("save_task_id", taskId);
    setSavingState(name);
    connectSaveSocket();
};

// ================================
// Init
// ================================

document.addEventListener("DOMContentLoaded", () => {

    if (localStorage.getItem("save_in_progress")) {

        updateHeaderIndicator(true);
        connectSaveSocket();

        const name = localStorage.getItem("save_list_name");
        if (name) showToast(name);
    }
});