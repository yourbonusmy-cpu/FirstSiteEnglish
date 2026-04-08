import spacy
import re
import sys
from pathlib import Path

nlp = spacy.load("en_core_web_sm")


def clean_srt(text: str) -> str:
    """
    Удаляет таймкоды, номера строк и мусор из .srt
    """
    # Удаляем таймкоды
    text = re.sub(r"\d{2}:\d{2}:\d{2},\d{3} --> .*", "", text)
    # Удаляем номера строк
    text = re.sub(r"^\d+$", "", text, flags=re.MULTILINE)
    return text


def extract_dictionary_units(text: str):
    doc = nlp(text)
    compounds = set()

    # 🔥 1. Ищем составные: (ADJ or NOUN) + NOUN
    for token in doc:
        if token.pos_ == "NOUN":
            for left in token.lefts:
                if left.pos_ in ["ADJ", "NOUN"]:
                    phrase = f"{left.lemma_.lower()} {token.lemma_.lower()}"
                    compounds.add(phrase)

    # 🔥 2. Одиночные существительные
    singles = set(
        token.lemma_.lower()
        for token in doc
        if token.pos_ == "NOUN" and not token.is_stop and token.is_alpha
    )

    # 🔥 3. Удаляем одиночные, если входят в составные
    for comp in compounds:
        for word in comp.split():
            singles.discard(word)

    return sorted(compounds | singles)


def process_file(uri: str):
    path = Path(uri)

    if not path.exists():
        print("❌ Файл не найден")
        return

    text = path.read_text(encoding="utf-8")

    if path.suffix.lower() == ".srt":
        text = clean_srt(text)

    words = extract_dictionary_units(text)

    print("\n📚 Найденные слова:\n")
    for w in words:
        print(w)

    print(f"\nВсего: {len(words)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("python extract_words.py /path/to/file.srt")
    else:
        process_file(sys.argv[1])
