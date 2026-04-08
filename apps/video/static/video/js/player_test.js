const player = document.getElementById("player");
const video = document.getElementById("video");

// HLS source
const hlsSource = "/media/hls/test/index.m3u8";

// Подключаем HLS
if (Hls.isSupported()) {
    const hls = new Hls();
    hls.loadSource(hlsSource);
    hls.attachMedia(video);
} else if (video.canPlayType("application/vnd.apple.mpegurl")) {
    video.src = hlsSource;
}

// Контролы
const playPause = document.getElementById("playPause");
const overlay = document.getElementById("overlay");
const progress = document.getElementById("progress");
const currentTimeEl = document.getElementById("currentTime");
const durationEl = document.getElementById("duration");
const volume = document.getElementById("volume");
const mute = document.getElementById("mute");
const fullscreen = document.getElementById("fullscreen");

let hideTimer;

/* ===== helpers ===== */
function formatTime(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
}

/* ===== play / pause ===== */
function togglePlay() {
    if (video.paused) {
        video.play();
        playPause.innerHTML = '<i class="bi bi-pause-fill"></i>';
    } else {
        video.pause();
        playPause.innerHTML = '<i class="bi bi-play-fill"></i>';
    }
}

playPause.onclick = togglePlay;
overlay.onclick = togglePlay;

/* ===== duration ===== */
video.addEventListener("loadedmetadata", () => {
    durationEl.textContent = formatTime(video.duration);
});

/* ===== progress ===== */
video.addEventListener("timeupdate", () => {
    if (video.duration) {
        const percent = (video.currentTime / video.duration) * 100;
        progress.value = percent;
        currentTimeEl.textContent = formatTime(video.currentTime);

        // закрашиваем просмотренное время
        progress.style.background = `linear-gradient(to right, darkred ${percent}%, rgba(255,255,255,0.3) ${percent}%)`;
    }
});

progress.oninput = () => {
    video.currentTime = (progress.value / 100) * video.duration;
};

/* ===== volume ===== */
volume.oninput = () => {
    video.volume = volume.value;
    video.muted = false;
    mute.innerHTML = '<i class="bi bi-volume-up"></i>';
};

mute.onclick = () => {
    video.muted = !video.muted;
    mute.innerHTML = video.muted
        ? '<i class="bi bi-volume-mute"></i>'
        : '<i class="bi bi-volume-up"></i>';
};

/* ===== fullscreen ===== */
fullscreen.onclick = () => {
    if (!document.fullscreenElement) {
        player.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
};

/* ===== auto-hide controls + cursor ===== */
function showControls() {
    player.classList.add("show-controls");
    player.classList.remove("hide-cursor"); // показываем курсор

    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
        player.classList.remove("show-controls");
        player.classList.add("hide-cursor"); // скрываем курсор
    }, 500);
}

player.addEventListener("mousemove", showControls);
player.addEventListener("mouseenter", showControls);
player.addEventListener("touchstart", showControls);

// сразу скрываем контролы и курсор через 1.5сек
hideTimer = setTimeout(() => {
    player.classList.remove("show-controls");
    player.classList.add("hide-cursor");
}, 500);

/* ===== keyboard controls ===== */
document.addEventListener("keydown", e => {
    if (e.target.tagName === "INPUT") return;
    if (e.code === "Space") {
        e.preventDefault();
        togglePlay();
    }
    if (e.code === "ArrowRight") video.currentTime += 5;
    if (e.code === "ArrowLeft") video.currentTime -= 5;
});
