import re
from collections import Counter
from dataclasses import dataclass, asdict
from typing import List, Tuple

from nltk import pos_tag
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

from apps.dictionary.models import Word

LEMMATIZER = WordNetLemmatizer()
STOP_WORDS = set(stopwords.words("english"))


@dataclass(slots=True)
class SubtitleWord:
    id: int
    name: str
    frequency: int


class ConvertTextToSubtitleWords:
    keep_pos = {"NOUN", "VERB", "ADJ"}
    min_len = 2

    def __init__(self, text: str, redis_client=None, task_id: str | None = None):
        self.redis_client = redis_client
        self.task_id = task_id
        self.subtitle_words: List[SubtitleWord] = self._convert(text)

    # ==================================================
    # Progress
    # ==================================================

    def _update_progress(self, percent: int) -> None:
        if self.redis_client and self.task_id:
            self.redis_client.set(
                f"subtitle:{self.task_id}:progress",
                percent,
            )

    # ==================================================
    # Main
    # ==================================================

    def _convert(self, text: str) -> List[SubtitleWord]:
        self._update_progress(0)

        text = self._clean_text(text)
        self._update_progress(10)

        tagged_tokens = self._tokenize(text)
        self._update_progress(20)

        counter, order = self._get_word_frequencies(tagged_tokens)
        self._update_progress(65)

        existing = self._map_existing_words(counter.keys())
        self._update_progress(85)

        result = self._build_subtitle_words(counter, order, existing)
        self._update_progress(100)

        return result

    # ==================================================
    # Text cleaning
    # ==================================================

    def _clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"\d*:\d*:.*\n", " ", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[0-9]", " ", text)
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # ==================================================
    # Tokenize + POS
    # ==================================================

    def _tokenize(self, text: str) -> List[Tuple[str, str]]:
        tokens = word_tokenize(text)
        return pos_tag(tokens)

    # ==================================================
    # Frequencies
    # ==================================================

    def _get_word_frequencies(
        self,
        tagged_tokens: List[Tuple[str, str]],
    ) -> tuple[Counter[str], dict[str, int]]:
        counter: Counter[str] = Counter()
        order: dict[str, int] = {}
        idx = 0
        total = len(tagged_tokens) or 1

        for i, (token, tag) in enumerate(tagged_tokens):
            if token in STOP_WORDS or len(token) < self.min_len:
                continue

            wn_pos = self._map_pos(tag)
            if not wn_pos:
                continue

            lemma = LEMMATIZER.lemmatize(token, wn_pos).lower()
            counter[lemma] += 1

            if lemma not in order:
                order[lemma] = idx
                idx += 1

            if i % 500 == 0:
                self._update_progress(20 + int(i / total * 45))

        return counter, order

    # ==================================================
    # POS mapping
    # ==================================================

    def _map_pos(self, nltk_pos: str) -> str | None:
        if nltk_pos.startswith("N") and "NOUN" in self.keep_pos:
            return wordnet.NOUN
        if nltk_pos.startswith("V") and "VERB" in self.keep_pos:
            return wordnet.VERB
        if nltk_pos.startswith("J") and "ADJ" in self.keep_pos:
            return wordnet.ADJ
        return None

    # ==================================================
    # DB check
    # ==================================================

    def _map_existing_words(self, lemmas) -> set[str]:
        return set(Word.objects.filter(name__in=lemmas).values_list("name", flat=True))

    # ==================================================
    # Build result (ONLY existing words)
    # ==================================================

    def _build_subtitle_words(
        self,
        counter: Counter[str],
        order: dict[str, int],
        existing: set[str],
    ) -> List[SubtitleWord]:
        result: List[SubtitleWord] = []

        for lemma, idx in sorted(order.items(), key=lambda x: x[1]):
            if lemma not in existing:
                continue

            result.append(
                SubtitleWord(
                    id=idx,
                    name=lemma,
                    frequency=counter[lemma],
                )
            )

        return result

    # ==================================================
    # Public API (как у остальных парсеров)
    # ==================================================

    def to_dict(self) -> List[dict]:
        return [asdict(w) for w in self.subtitle_words]
