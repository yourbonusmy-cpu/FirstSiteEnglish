import os
import re
from collections import Counter
from typing import List

import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag

from apps.dictionary.models import Word

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))


class SubtitleWord:
    def __init__(
        self,
        name: str,
        frequency: int,
        transcription: str = "",
        selected_pos: str = "",
        selected_translation: str = "",
        pos_list: list[str] | None = None,
        translations_for_pos: dict[str, list[str]] | None = None,
    ):
        self.name = name
        self.frequency = frequency
        self.transcription = transcription
        self.selected_pos = selected_pos
        self.selected_translation = selected_translation
        self.pos_list = pos_list or []
        self.translations_for_pos = translations_for_pos or {}


class ConvertTextToSubtitleWords:
    keep_pos = {"NOUN", "VERB", "ADJ"}
    min_len = 2

    def __init__(self, text: str):
        self.subtitle_words: List[SubtitleWord] = self._convert(text)

    def _convert(self, text: str) -> List[SubtitleWord]:
        text = self._clean_text(text)
        word_counter = self._get_word_frequencies(text)
        return self._map_existing_words(word_counter)

    def _clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"\d*:\d*:.*\n", "", text)
        text = re.sub(r"<[^>]*>", "", text)
        text = re.sub(r"\n+", " ", text)
        text = re.sub(r"[0-9]", "", text)
        text = re.sub(r"[^\w\s]", " ", text)
        return text.strip()

    def _chunked(self, seq, size: int):
        for i in range(0, len(seq), size):
            yield seq[i : i + size]

    def _get_word_frequencies(self, text: str) -> Counter:
        # Самый быстрый токенайзер для уже очищенного текста
        tokens = text.split()

        # Ранняя фильтрация: меньше токенов → быстрее POS
        tokens = [t for t in tokens if len(t) >= self.min_len and t not in stop_words]

        counter = Counter()

        # POS-теггинг батчами (уменьшаем нагрузку на память)
        for chunk in self._chunked(tokens, 2000):
            tagged_tokens = pos_tag(chunk)

            for token, tag in tagged_tokens:
                wn_pos = self._map_pos(tag)
                if not wn_pos:
                    continue

                lemma = lemmatizer.lemmatize(token, wn_pos)
                counter[lemma.lower()] += 1

        return counter

    def _map_pos(self, nltk_pos: str) -> str | None:
        """
        NLTK POS → WordNet POS
        """
        if nltk_pos.startswith("N") and "NOUN" in self.keep_pos:
            return wordnet.NOUN
        if nltk_pos.startswith("V") and "VERB" in self.keep_pos:
            return wordnet.VERB
        if nltk_pos.startswith("J") and "ADJ" in self.keep_pos:
            return wordnet.ADJ
        return None

    def _map_existing_words(self, word_counter: Counter) -> List[SubtitleWord]:
        subtitle_words = []

        existing_words_qs = Word.objects.filter(
            name__in=word_counter.keys()
        ).prefetch_related(
            "word_parts__part_of_speech",
            "word_parts__translations",
        )

        for word in existing_words_qs:
            frequency = word_counter.get(word.name, 0)
            if frequency == 0:
                continue

            pos_objs = list(word.word_parts.all())
            pos_list = [wp.part_of_speech.name for wp in pos_objs]

            main_pos_obj = next(
                (wp for wp in pos_objs if wp.is_main), pos_objs[0] if pos_objs else None
            )
            if not main_pos_obj:
                continue

            selected_pos = main_pos_obj.part_of_speech.name

            translations_for_pos = {
                wp.part_of_speech.name: [t.translation for t in wp.translations.all()]
                for wp in pos_objs
            }

            main_translation_obj = main_pos_obj.translations.filter(
                is_main=True
            ).first()

            if main_translation_obj:
                selected_translation = main_translation_obj.translation
            elif translations_for_pos.get(selected_pos):
                selected_translation = translations_for_pos[selected_pos][0]
            else:
                selected_translation = ""

            subtitle_words.append(
                SubtitleWord(
                    name=word.name,
                    frequency=frequency,
                    transcription=word.transcription,
                    selected_pos=selected_pos,
                    selected_translation=selected_translation,
                    pos_list=pos_list,
                    translations_for_pos=translations_for_pos,
                )
            )

        return subtitle_words

    def to_dict(self) -> List[dict]:
        return [
            {
                "name": w.name,
                "transcription": w.transcription,
                "frequency": w.frequency,
                "pos_list": w.pos_list,
                "selected_pos": w.selected_pos,
                "translations_for_pos": w.translations_for_pos,
                "selected_translation": w.selected_translation,
            }
            for w in self.subtitle_words
        ]
