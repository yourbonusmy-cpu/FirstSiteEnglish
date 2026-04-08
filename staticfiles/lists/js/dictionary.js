let page = 1;
let hasNext = true;
let loading = false;
let query = "";

const container = document.getElementById("wordsContainer");
const loader = document.getElementById("loader");
const sentinel = document.getElementById("sentinel");
const searchInput = document.getElementById("searchInput");
const apiUrl = searchInput.dataset.apiUrl;

async function loadWords(reset=false) {
    if (loading || !hasNext) return;

    loading = true;
    loader.style.display = "block";

    const response = await fetch(`${apiUrl}?page=${page}&q=${query}`);
    const data = await response.json();

    if (reset) {
        container.innerHTML = "";
        page = 1;
    }

    data.results.forEach(word => {
        const div = document.createElement("div");
        div.className = "card mb-2 p-3";
        div.innerHTML = `
            <strong>${word.name}</strong>
            <span class="text-muted">${word.transcription || ""}</span>
            <div>
                ${word.parts_of_speech.map(pos =>
                    `<div><em>${pos.name}</em>: ${pos.translations.join(", ")}</div>`
                ).join("")}
            </div>
        `;
        container.appendChild(div);
    });

    hasNext = data.has_next;
    page++;

    loading = false;
    loader.style.display = "none";

    observer.unobserve(sentinel);
    observer.observe(sentinel);
}

const observer = new IntersectionObserver(
    entries => {
        if (entries[0].isIntersecting) loadWords();
    },
    { rootMargin: "200px" }
);

searchInput.addEventListener("input", () => {
    page = 1;
    hasNext = true;
    query = searchInput.value;
    loadWords(true);
});

loadWords();
observer.observe(sentinel);
