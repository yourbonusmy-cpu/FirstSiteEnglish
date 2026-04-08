let index = 0;

const card = document.getElementById("card");
const wordEl = document.getElementById("word");
const transcriptionEl = document.getElementById("transcription");
const translationEl = document.getElementById("translation");
const answerEl = document.getElementById("answer");

const currentIndexEl = document.getElementById("current-index");
const totalWordsEl = document.getElementById("total-words");

totalWordsEl.textContent = WORDS.length;

function renderCard() {
  const w = WORDS[index];

  wordEl.textContent = w.word;
  transcriptionEl.textContent = w.transcription || "";
  translationEl.textContent = w.main_translation || "";

  answerEl.value = "";
  card.classList.remove("flipped");

  // прогресс
  currentIndexEl.textContent = index + 1;
}

card.addEventListener("click", () => {
  card.classList.toggle("flipped");
});

document.getElementById("next").onclick = () => {
  index = (index + 1) % WORDS.length;
  renderCard();
};

document.getElementById("prev").onclick = () => {
  index = (index - 1 + WORDS.length) % WORDS.length;
  renderCard();
};

function checkAnswer() {
  const input = answerEl.value.trim().toLowerCase();
  const correctAnswers = WORDS[index].all_translations;

  if (!input) return;

  if (correctAnswers.includes(input)) {
    card.classList.add("flipped");
    alert("Верно");
  } else {
    alert("Неверно");
  }
}

document.getElementById("check").onclick = checkAnswer;

/* ENTER */
answerEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    checkAnswer();
  }
});

renderCard();
