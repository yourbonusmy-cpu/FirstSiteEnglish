from collections import Counter
from dataclasses import dataclass, asdict
from typing import List
import re
import time

from apps.dictionary.models import Word
from apps.ingestion.services.nlp_loader_spacy import load_nlp_spacy


@dataclass(slots=True)
class SubtitleWord:
    id: int
    name: str
    frequency: int


class ConvertTextToSubtitleWords:
    min_len = 2

    def __init__(self, text: str, task_id: str | None = None, redis_client=None):
        self.nlp = load_nlp_spacy()
        self.task_id = task_id
        self.redis_client = redis_client
        self.subtitle_words: List[SubtitleWord] = self._convert(text)

    def _convert(self, text: str) -> List[SubtitleWord]:
        s_t = time.perf_counter()
        self._update_progress(0)

        text = self._clean_text(text)
        self._update_progress(5)

        counter = Counter()
        min_len = self.min_len
        doc = self.nlp(text)
        self._update_progress(80)

        for token in doc:
            if not token.is_alpha:
                continue
            lemma = token.lemma_
            if len(lemma) < min_len:
                continue
            counter[lemma] += 1

        self._update_progress(95)

        result = self._map_existing_words(counter)

        self._update_progress(100)

        print(f"time: {time.perf_counter() - s_t}")
        return result

    def _map_existing_words(self, counter: Counter) -> List[SubtitleWord]:
        if not counter:
            return []

        existing_words_qs = Word.objects.filter(name__in=counter.keys()).only(
            "id", "name"
        )

        existing_words_dict = {w.name: w for w in existing_words_qs}

        subtitle_words = []

        # порядок появления сохраняется
        for lemma, freq in counter.items():
            word = existing_words_dict.get(lemma)
            if word:
                subtitle_words.append(
                    SubtitleWord(
                        id=word.id,
                        name=word.name,
                        frequency=freq,
                    )
                )

        return subtitle_words

    def _update_progress(self, percent: int):
        if self.redis_client and self.task_id:
            self.redis_client.set(f"subtitle:{self.task_id}:progress", percent)

    def _clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"\d*:\d*:.*\n", "", text)
        text = re.sub(r"<[^>]*>", "", text)
        text = re.sub(r"[0-9]", "", text)
        text = re.sub(r"[♪♫]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def to_dict(self) -> List[dict]:
        return [asdict(w) for w in self.subtitle_words]
