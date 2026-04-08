document.addEventListener("DOMContentLoaded", () => {

    // Берем JSON из data-words
    const root = document.getElementById("study-root");
    const words = JSON.parse(document.getElementById("study-root").dataset.words);
    console.log(words);  // <-- убедись, что массив выводится

    let currentIndex = 0;
    let correctCount = 0;
    let seconds = 0;

    const card = document.getElementById("word-card");
    const wordEl = document.getElementById("word");
    const transcriptionEl = document.getElementById("transcription");
    const back = document.getElementById("card-back");
    const answersDiv = document.getElementById("answer-options");
    const progressBar = document.getElementById("progress-bar");
    const scoreDiv = document.getElementById("score");

    const timerDiv = document.getElementById("timer");
    const nextBtn = document.getElementById("next-btn");
    const prevBtn = document.getElementById("prev-btn");
    const finishBtn = document.getElementById("finish-btn");

    // Таймер
    setInterval(() => {
        seconds++;
        const m = String(Math.floor(seconds / 60)).padStart(2, '0');
        const s = String(seconds % 60).padStart(2, '0');
        timerDiv.innerText = `${m}:${s}`;
    }, 1000);

    // События
    card.addEventListener("click", flipCard);
    nextBtn.addEventListener("click", nextWord);
    prevBtn.addEventListener("click", prevWord);
    finishBtn.addEventListener("click", finishStudy);

    // Функции
    function showWord() {
        card.classList.remove("flipped");
        const wordObj = words[currentIndex];
        wordEl.innerText = wordObj.word;
        transcriptionEl.innerText = wordObj.transcription;
        back.innerText = wordObj.main_translation;

        // Варианты ответов
        const options = [
            wordObj.main_translation,
            ...wordObj.all_translations.filter(t => t !== wordObj.main_translation)
        ].slice(0, 4);
        while (options.length < 4) options.push("...");
        options.sort(() => Math.random() - 0.5);

        answersDiv.innerHTML = "";
        options.forEach(opt => {
            const btn = document.createElement("button");
            btn.innerText = opt;
            btn.addEventListener("click", () => checkAnswer(btn, wordObj.main_translation));
            answersDiv.appendChild(btn);
        });

        progressBar.innerText = `${currentIndex+1} / ${words.length}`;
    }

    function flipCard() {
        card.classList.toggle("flipped");
    }

    function checkAnswer(btn, correct) {
        if (btn.innerText === correct) {
            btn.classList.add("correct");
            correctCount++;
        } else {
            btn.classList.add("wrong");
        }
        scoreDiv.innerText = `Правильных: ${correctCount}`;
    }

    function nextWord() {
        currentIndex = (currentIndex + 1) % words.length;
        showWord();
    }

    function prevWord() {
        currentIndex = (currentIndex - 1 + words.length) % words.length;
        showWord();
    }

    function finishStudy() {
        alert(`Вы завершили изучение. Правильных: ${correctCount}/${words.length}`);
    }

    showWord();
});
