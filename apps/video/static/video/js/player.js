const video = document.getElementById("video");
const subtitleLayer = document.getElementById("subtitle-layer");

let subtitles = [];

fetch(SUBTITLE_JSON_URL)
  .then(r => r.json())
  .then(data => {
    subtitles = data;
    video.addEventListener("timeupdate", onTimeUpdate);
  })
  .catch(console.error);

function onTimeUpdate() {
  const time = video.currentTime;
  const active = subtitles.find(s => time >= s.start && time <= s.end);

  if (!active) {
    subtitleLayer.innerHTML = "";
    return;
  }

  subtitleLayer.innerHTML = active.tokens
    .map(t => `<span data-lemma="${t.lemma}">${t.raw}</span>`)
    .join(" "); // пробелы между словами
}
const videoContainer = document.getElementById("video-container");
const fsBtn = document.getElementById("fs-btn");

fsBtn.addEventListener("click", () => {
  if (document.fullscreenElement) {
    document.exitFullscreen();
  } else {
    videoContainer.requestFullscreen();
  }
});
