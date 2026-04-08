// ==========================
// DATA
// ==========================
const words = window.STUDY_WORDS || [];

let currentIndex = 0;
let correctCount = 0;

// состояние для каждого слова
const state = {};

words.forEach(w => {
    state[w.word] = {
        slots: Array(w.word.length).fill(null),
        letters: shuffle(w.word.split("")),
        is_correct: false,
        locked: false
    };
});

// ==========================
// DOM
// ==========================
const translateDiv = document.getElementById('puzzle-translate');
const slotsDiv = document.getElementById('puzzle-slots');
const lettersDiv = document.getElementById('puzzle-letters');
const progressDiv = document.getElementById('puzzle-progress');
const timerDiv = document.getElementById('timer');
const scoreDiv = document.getElementById('score');
const clearBtn = document.getElementById('clear-btn');

// ==========================
// TIMER
// ==========================
let seconds = 0;
const timerInterval = setInterval(() => {
    seconds++;
    const m = String(Math.floor(seconds / 60)).padStart(2,'0');
    const s = String(seconds % 60).padStart(2,'0');
    if (timerDiv) timerDiv.innerText = `${m}:${s}`;
}, 1000);

window.addEventListener("beforeunload", () => clearInterval(timerInterval));

// ==========================
// RENDER
// ==========================
function showWord() {
    if (!words.length) return;
    const wordObj = words[currentIndex];
    const st = state[wordObj.word];

    translateDiv.innerText = wordObj.main_translation;

    renderSlots(wordObj.word, st);
    renderLetters(st);

    progressDiv.innerText = `${currentIndex + 1} / ${words.length}`;
    scoreDiv.innerText = `${correctCount} / ${words.length}`;
}

// слоты
function renderSlots(word, st) {
    slotsDiv.innerHTML = '';
    st.slots.forEach((char, i) => {
        const span = document.createElement('span');
        span.innerText = char || '';
        if (st.is_correct || (char && char === word[i])) span.classList.add('correct');
        span.onclick = () => removeFromSlot(word, i);
        slotsDiv.appendChild(span);
    });
}

// буквы
function renderLetters(st) {
    lettersDiv.innerHTML = '';
    st.letters.forEach((char, i) => {
        const span = document.createElement('span');
        span.innerText = char || '';
        if (!char) span.classList.add('used');
        span.onclick = () => placeLetter(i);
        lettersDiv.appendChild(span);
    });
}

// ==========================
// ACTIONS
// ==========================
function placeLetter(letterIndex) {
    const wordObj = words[currentIndex];
    const st = state[wordObj.word];
    if (st.locked) return;
    const emptyIndex = st.slots.indexOf(null);
    if (emptyIndex === -1 || !st.letters[letterIndex]) return;

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

if (clearBtn) {
    clearBtn.onclick = () => {
        const wordObj = words[currentIndex];
        state[wordObj.word] = {
            slots: Array(wordObj.word.length).fill(null),
            letters: shuffle(wordObj.word.split("")),
            is_correct: false,
            locked: false
        };
        showWord();
    };
}

// ==========================
// CHECK
// ==========================
function afterChange(wordObj) {
    const st = state[wordObj.word];
    renderSlots(wordObj.word, st);
    renderLetters(st);

    if (!st.slots.includes(null)) {
        if (st.slots.join('') === wordObj.word) onCorrect(wordObj);
    }
}

function onCorrect(wordObj) {
    const st = state[wordObj.word];
    if (st.is_correct) return;

    st.is_correct = true;
    st.locked = true;
    correctCount++;
    scoreDiv.innerText = `${correctCount} / ${words.length}`;

    showWord();
    setTimeout(() => nextWord(), 700);
}

// ==========================
// NAVIGATION
// ==========================
function nextWord() {
    if (currentIndex < words.length - 1) currentIndex++;
    showWord();
}
function prevWord() {
    if (currentIndex > 0) currentIndex--;
    showWord();
}

// ==========================
// FINISH
// ==========================
function finishStudy() {
    clearInterval(timerInterval);
    alert(`Вы завершили изучение. Правильных: ${correctCount} / ${words.length}`);
}

// ==========================
// UTILS
// ==========================
function shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

// ==========================
// KEYBOARD INPUT
// ==========================
document.addEventListener('keydown', (e) => {
    const wordObj = words[currentIndex];
    const st = state[wordObj.word];
    if (!wordObj || st.locked) return;

    const key = e.key.toUpperCase();

    // Backspace → удаляем последнюю введённую букву
    if (e.key === 'Backspace') {
        for (let i = st.slots.length - 1; i >= 0; i--) {
            if (st.slots[i] !== null) {
                removeFromSlot(wordObj.word, i);
                break;
            }
        }
        e.preventDefault();  // предотвращаем переход браузера назад
        return;
    }

    // Проверка буквы (если есть в puzzle-letters)
    const letterIndex = st.letters.findIndex(l => l && l.toUpperCase() === key);
    if (letterIndex !== -1) {
        placeLetter(letterIndex);
    }
});

// ==========================
// START
// ==========================
showWord();