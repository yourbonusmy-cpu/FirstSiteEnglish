let index = 0;
let correctCount = 0;

/* =======================
   TIMER STATE
======================= */
let seconds = 0;
let timerInterval = null;
let timerRunning = false;

/* =======================
   DOM ELEMENTS
======================= */
const card = document.getElementById("card");
const wordEl = document.getElementById("word");
const transcriptionEl = document.getElementById("transcription");
const translationEl = document.getElementById("translation");
const answerEl = document.getElementById("answer");
const feedbackEl = document.getElementById("feedback");

const currentIndexEl = document.getElementById("current-index");
const totalWordsEls = document.querySelectorAll(".total-words"); // ✅ ИСПРАВЛЕНО
const correctCountEl = document.getElementById("correct-count");
const timerEl = document.getElementById("timer");

const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");
const checkBtn = document.getElementById("check");
const finishBtn = document.getElementById("finish");

/* =======================
   INIT
======================= */
totalWordsEls.forEach(el => el.textContent = WORDS.length);

// служебные поля
WORDS.forEach(w => {
  w.done = false;
  w.userAnswer = "";
});

/* =======================
   TIMER LOGIC
======================= */
function renderTimer() {
  const mins = String(Math.floor(seconds / 60)).padStart(2, "0");
  const secs = String(seconds % 60).padStart(2, "0");
  timerEl.textContent = `${mins}:${secs}`;
}

function startTimer() {
  if (timerRunning) return;

  timerRunning = true;
  timerInterval = setInterval(() => {
    seconds++;
    renderTimer();
  }, 1000);
}

function stopTimer() {
  timerRunning = false;
  clearInterval(timerInterval);
  timerInterval = null;
}

/* ⏸ пауза таймера при уходе со страницы */
document.addEventListener("visibilitychange", () => {
  document.hidden ? stopTimer() : startTimer();
});

/* =======================
   UI HELPERS
======================= */
function updateCorrectCount() {
  correctCountEl.textContent = correctCount;
}

/* =======================
   CARD RENDER
======================= */
function renderCard() {
  const w = WORDS[index];

  wordEl.textContent = w.word;
  transcriptionEl.textContent = w.transcription || "";
  translationEl.textContent = w.main_translation || "";

  answerEl.value = w.userAnswer || "";
  feedbackEl.textContent = "";

  // сброс состояния
  answerEl.classList.remove("correct");
  answerEl.disabled = false;
  checkBtn.disabled = false;

  if (w.done) {
    answerEl.classList.add("correct");
    answerEl.disabled = true;
    checkBtn.disabled = true;
  }

  card.classList.toggle("flipped", w.done);

  currentIndexEl.textContent = index + 1;
  totalWordsEls.forEach(el => el.textContent = WORDS.length);
}

/* =======================
   CHECK ANSWER
======================= */
function checkAnswer() {
  const input = answerEl.value.trim().toLowerCase();
  if (!input) return;

  const w = WORDS[index];
  w.userAnswer = input;

  if (w.all_translations.includes(input)) {
    if (!w.done) {
      w.done = true;
      correctCount++;
      updateCorrectCount();
    }

    feedbackEl.textContent = "Верно!";
    feedbackEl.style.color = "green";

    answerEl.classList.add("correct");
    answerEl.disabled = true;
    checkBtn.disabled = true;
    card.classList.add("flipped");
  } else {
    feedbackEl.textContent = "Неверно!";
    feedbackEl.style.color = "red";
    answerEl.classList.remove("correct");
  }
}

/* =======================
   EVENTS
======================= */
card.addEventListener("click", () => {
  card.classList.toggle("flipped");
});

prevBtn.onclick = () => {
  index = (index - 1 + WORDS.length) % WORDS.length;
  renderCard();
};

nextBtn.onclick = () => {
  index = (index + 1) % WORDS.length;
  renderCard();
};

checkBtn.onclick = checkAnswer;

answerEl.addEventListener("keydown", e => {
  if (e.key === "Enter") {
    e.preventDefault();
    checkAnswer();
  }
});

finishBtn.onclick = () => {
  stopTimer();
  alert(
    `Тест завершен!\n` +
    `Правильных: ${correctCount} из ${WORDS.length}\n` +
    `Время: ${timerEl.textContent}`
  );
};

/* =======================
   START
======================= */
renderCard();
renderTimer();
startTimer();
