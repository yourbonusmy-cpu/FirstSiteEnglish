# ingestion/services/phrasal_extractor.py
import re
from collections import defaultdict
from pathlib import Path
import spacy

# Инициализация spaCy один раз
nlp = spacy.load("en_core_web_sm", disable=["ner", "parser", "textcat"])


class PhrasalExtractor:
    """
    Класс для извлечения слов и фразовых глаголов из текста.
    Поддерживает gap (разрыв между словами фразового глагола) и фильтрует короткие слова.
    """

    def __init__(self, phrasal_verbs_path: str, max_gap: int = 2):
        self.max_gap = max_gap
        self.phrasal_verbs = self.load_phrasal_verbs(phrasal_verbs_path)
        self.pv_index = self.build_pv_index(self.phrasal_verbs)

    # -----------------------
    # Очистка текста
    # -----------------------
    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r"^\d+\s*$", " ", text, flags=re.MULTILINE)
        text = re.sub(r"\d+:\d+:\d+[,.]\d+.*\n", " ", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # -----------------------
    # Загрузка фразовых глаголов
    # -----------------------
    @staticmethod
    def load_phrasal_verbs(path: str) -> set[str]:
        verbs = set()
        with open(path, encoding="utf-8") as f:
            for line in f:
                v = re.sub(r"\s+", " ", line.strip().lower())
                if v:
                    verbs.add(v)
        return verbs

    # -----------------------
    # Индексирование для быстрого поиска
    # -----------------------
    @staticmethod
    def build_pv_index(phrasal_verbs: set[str]) -> dict[str, list[list[str]]]:
        index = defaultdict(list)
        for pv in phrasal_verbs:
            parts = pv.split()
            index[parts[0]].append(parts[1:])
        # длинные хвосты первыми
        for verb in index:
            index[verb].sort(key=lambda x: -len(x))
        return index

    # -----------------------
    # Лемма слова
    # -----------------------
    @staticmethod
    def get_lemma(token) -> str:
        return token.lemma_.lower()

    # -----------------------
    # Основной метод извлечения
    # -----------------------
    def extract(self, text: str) -> dict[str, int]:
        """
        Возвращает словарь {слово/фразовый глагол: частота}
        """
        text = self.clean_text(text)
        doc = nlp(text)
        lemmas = [t.lemma_.lower() for t in doc if t.is_alpha]

        result = {}
        i = 0

        while i < len(lemmas):
            lemma = lemmas[i]
            matched = None
            end_pos = None

            candidates = self.pv_index.get(lemma)

            if candidates:
                # 1️⃣ проверяем строго подряд
                for tail in candidates:
                    length = len(tail)
                    if lemmas[i + 1 : i + 1 + length] == tail:
                        matched = lemma + " " + " ".join(tail)
                        end_pos = i + 1 + length
                        break

                # 2️⃣ проверяем с gap
                if not matched:
                    for tail in candidates:
                        j = i + 1
                        gaps = 0
                        found = 0
                        while (
                            j < len(lemmas)
                            and gaps <= self.max_gap
                            and found < len(tail)
                        ):
                            if lemmas[j] == tail[found]:
                                found += 1
                            else:
                                gaps += 1
                            j += 1
                        if found == len(tail):
                            matched = lemma + " " + " ".join(tail)
                            end_pos = j
                            break

            if matched:
                # ✅ фразовые глаголы всегда добавляем
                result[matched] = result.get(matched, 0) + 1
                i = end_pos
            else:
                # ⚠️ одиночные слова, длина >= 3
                if len(lemma) >= 3:
                    result[lemma] = result.get(lemma, 0) + 1
                i += 1

        return result


# -----------------------
# Удобный singleton для проекта
# -----------------------
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
pv_path = BASE_DIR / "fixtures" / "phrasal_verbs_cleaned_640.txt"
_PHRASES_PATH = pv_path
_extractor_instance = None


def get_phrasal_extractor() -> PhrasalExtractor:
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = PhrasalExtractor(phrasal_verbs_path=_PHRASES_PATH)
    return _extractor_instance
