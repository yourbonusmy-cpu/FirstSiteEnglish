/* ================================
   DATA & STATE
================================ */

const words = window.STUDY_WORDS;

let currentIndex = 0;
let score = 0;
let isFinished = false;

// runtime state per word
const state = {};

words.forEach(w => {
    state[w.word] = {
        slots: Array(w.word.length).fill(null),
        letters: shuffle(w.word.split("")),
        is_correct: false,
        locked: false
    };
});

/* ================================
   DOM
================================ */

const translateEl = document.getElementById("word-translate");
const slotsEl = document.getElementById("word-slots");
const lettersEl = document.getElementById("letters");
const progressEl = document.getElementById("progress");
const scoreEl = document.getElementById("score");

/* ================================
   TIMER
================================ */

let seconds = 0;
const timerId = setInterval(() => {
    if (isFinished) return;

    seconds++;
    const m = String(Math.floor(seconds / 60)).padStart(2, "0");
    const s = String(seconds % 60).padStart(2, "0");
    document.getElementById("timer").innerText = `${m}:${s}`;
}, 1000);

/* ================================
   RENDER
================================ */

function showWord() {
    const wordObj = words[currentIndex];
    const st = state[wordObj.word];

    translateEl.innerText = wordObj.main_translation;

    renderSlots(wordObj.word, st);
    renderLetters(st);

    progressEl.innerText = `${currentIndex + 1} / ${words.length}`;
    scoreEl.innerText = `Score: ${score}`;
}

function renderSlots(word, st) {
    slotsEl.innerHTML = "";

    st.slots.forEach((char, i) => {
        const span = document.createElement("span");
        span.innerText = char || "";

        if (st.is_correct) span.classList.add("correct");

        span.onclick = () => removeFromSlot(word, i);
        slotsEl.appendChild(span);
    });
}

function renderLetters(st) {
    lettersEl.innerHTML = "";

    st.letters.forEach((char, i) => {
        const span = document.createElement("span");
        span.innerText = char || "";
        if (!char) span.classList.add("used");

        span.onclick = () => placeLetter(i);
        lettersEl.appendChild(span);
    });
}

/* ================================
   ACTIONS
================================ */

function placeLetter(letterIndex) {
    const wordObj = words[currentIndex];
    const st = state[wordObj.word];

    if (st.locked) return;

    const emptyIndex = st.slots.indexOf(null);
    if (emptyIndex === -1) return;
    if (!st.letters[letterIndex]) return;

    st.slots[emptyIndex] = st.letters[letterIndex];
    st.letters[letterIndex] = null;

    afterChange(wordObj);
}

function removeFromSlot(word, slotIndex) {
    const st = state[word];

    if (st.locked) return;

    const char = st.slots[slotIndex];
    if (!char) return;

    const emptyLetterIndex = st.letters.indexOf(null);
    st.letters[emptyLetterIndex] = char;
    st.slots[slotIndex] = null;

    afterChange(words[currentIndex]);
}

function clearWord() {
    const wordObj = words[currentIndex];
    state[wordObj.word] = {
        slots: Array(wordObj.word.length).fill(null),
        letters: shuffle(wordObj.word.split("")),
        is_correct: false,
        locked: false
    };
    showWord();
}

/* ================================
   CHECK
================================ */

function afterChange(wordObj) {
    const st = state[wordObj.word];

    renderSlots(wordObj.word, st);
    renderLetters(st);

    if (!st.slots.includes(null)) {
        const assembled = st.slots.join("");

        if (assembled === wordObj.word) {
            onCorrect(wordObj);
        }
    }
}

function onCorrect(wordObj) {
    const st = state[wordObj.word];
    if (st.is_correct) return;

    st.is_correct = true;
    st.locked = true;

    if (score < 4) score++;

    sendAnswer(wordObj.word, true);
    showWord();
}

/* ================================
   NAVIGATION
================================ */

function nextWord() {
    if (isFinished) return;
    currentIndex = (currentIndex + 1) % words.length;
    showWord();
}

function prevWord() {
    if (isFinished) return;
    currentIndex = (currentIndex - 1 + words.length) % words.length;
    showWord();
}

/* ================================
   BACKEND
================================ */

function sendAnswer(word, isCorrect) {
    fetch("/study/submit-answer/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({
            word: word,
            is_correct: isCorrect
        })
    });
}

function getCSRFToken() {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="))
        ?.split("=")[1];
}

/* ================================
   UTILS
================================ */

function shuffle(arr) {
    return arr.sort(() => Math.random() - 0.5);
}

/* ================================
   START
================================ */

showWord();
