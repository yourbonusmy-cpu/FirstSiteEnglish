/* ================================
   ИСХОДНЫЕ ДАННЫЕ И СОСТОЯНИЕ
================================ */

const words = window.STUDY_WORDS;

let currentIndex = 0;
let correctCount = 0;
let isFinished = false;

// runtime-состояние для каждого слова
words.forEach(w => {
    w.user_attempts = [];   // все выбранные варианты
    w.is_correct = false;   // стал ли правильным
    w.locked = false;       // блокируется ТОЛЬКО после правильного
    w.impression_sent = false;
});

/* ================================
   DOM
================================ */

const card = document.getElementById("word-card");
const front = document.getElementById("card-front");
const back = document.getElementById("card-back");
const answersDiv = document.getElementById("answer-options");
const progressBar = document.getElementById("progress-bar");
const scoreDiv = document.getElementById("score");

const wordMain = document.getElementById("word-main");
const wordTranscription = document.getElementById("word-transcription");

/* ================================
   ТАЙМЕР
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
   ОТРИСОВКА
================================ */

function showWord() {
    const wordObj = words[currentIndex];

    card.classList.remove("flipped");

    wordMain.innerText = wordObj.word;
    wordTranscription.innerText = wordObj.transcription || "";
    back.innerText = wordObj.main_translation;


    if (!wordObj.impression_sent) {
        sendImpression(wordObj.word);
        wordObj.impression_sent = true;
    }

    renderAnswers(wordObj);
    restoreAttempts(wordObj);

    progressBar.innerText = `${currentIndex + 1} / ${words.length}`;
    updateScore();
}

function sendImpression(word) {
    fetch("/study/word-impression/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ word })
    });
}


function renderAnswers(wordObj) {
    answersDiv.innerHTML = "";

    let options = [];

    if (wordObj.distractors && wordObj.distractors.length === 3) {
        options = [...wordObj.distractors, wordObj.main_translation];
    } else if (wordObj.all_translations?.length) {
        options = [...wordObj.all_translations];
        while (options.length < 4) options.push("...");
        if (options.length > 4) options = shuffle(options).slice(0, 4);
    } else {
        options = [wordObj.main_translation];
        while (options.length < 4) options.push("...");
    }

    options = shuffle(options);

    options.forEach(opt => {
        const btn = document.createElement("button");
        btn.innerText = opt;

        btn.onclick = () => onAnswer(btn, wordObj);

        answersDiv.appendChild(btn);
    });
}

function flipCard() {
    card.classList.toggle("flipped");
}

/* ================================
   ЛОГИКА ОТВЕТА
================================ */

function onAnswer(btn, wordObj) {
    if (isFinished) return;
    if (wordObj.locked) return;

    const answer = btn.innerText;
    if (wordObj.user_attempts.includes(answer)) return;

    const isCorrect = answer === wordObj.main_translation;

    wordObj.user_attempts.push(answer);

    btn.classList.add(isCorrect ? "correct" : "wrong");

    sendAnswer(wordObj.word, isCorrect);

    if (isCorrect) {
        wordObj.is_correct = true;
        wordObj.locked = true;
        correctCount++;
        lockAnswers();
    }

    updateScore();
}

/* ================================
   ВОССТАНОВЛЕНИЕ СОСТОЯНИЯ
================================ */

function restoreAttempts(wordObj) {
    if (!wordObj.user_attempts.length) return;

    answersDiv.querySelectorAll("button").forEach(btn => {
        if (wordObj.user_attempts.includes(btn.innerText)) {
            const isCorrect = btn.innerText === wordObj.main_translation;
            btn.classList.add(isCorrect ? "correct" : "wrong");
        }

        if (wordObj.locked) {
            btn.disabled = true;
        }
    });
}

function lockAnswers() {
    answersDiv.querySelectorAll("button")
        .forEach(btn => btn.disabled = true);
}

/* ================================
   НАВИГАЦИЯ
================================ */

function nextWord() {
    if (isFinished) return;

    currentIndex = (currentIndex + 1) % words.length;
    showWord();
}

function prevWord() {
    if (isFinished) return;

    currentIndex =
        (currentIndex - 1 + words.length) % words.length;
    showWord();
}

/* ================================
   ЗАВЕРШЕНИЕ ТЕСТА
================================ */

function finishStudy() {
    if (isFinished) return;

    isFinished = true;
    clearInterval(timerId);

    lockAnswers();

    window.location.href = "/study/finish/";
}

/* ================================
   ВСПОМОГАТЕЛЬНОЕ
================================ */

function updateScore() {
    scoreDiv.innerText = `Правильных: ${correctCount} / ${words.length}`;
}

function shuffle(arr) {
    return arr.sort(() => Math.random() - 0.5);
}

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
   СТАРТ
================================ */

showWord();
