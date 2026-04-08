import re
from collections import Counter
from typing import List, Tuple

from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk.corpus import wordnet

from apps.dictionary.models import Word
from .nlp_loader_nltk import LEMMATIZER, STOP_WORDS, WORDNET_MWES


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
    mwe_min = 2
    mwe_max = 4

    def __init__(self, text: str):
        self.subtitle_words: List[SubtitleWord] = self._convert(text)

    # -----------------------------
    # Основной pipeline
    # -----------------------------
    def _convert(self, text: str) -> List[SubtitleWord]:
        text = self._clean_text(text)

        # Токенизация + POS
        tokens = word_tokenize(text)
        tagged_tokens = pos_tag(tokens)

        lemmas = []
        for token, tag in tagged_tokens:
            token_lower = token.lower()
            if token_lower in STOP_WORDS or len(token_lower) < self.min_len:
                continue
            wn_pos = self._map_pos(tag)
            if not wn_pos:
                continue
            lemma = LEMMATIZER.lemmatize(token_lower, wn_pos)
            lemmas.append(lemma)

        # Объединяем MWEs + одиночные слова
        ordered_tokens, frequencies = self._process_mwes(lemmas)

        # Мапим на существующие слова в базе
        return self._map_existing_words(frequencies)

    # -----------------------------
    # Очистка текста
    # -----------------------------
    def _clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"\d*:\d*:.*\n", "", text)
        text = re.sub(r"<[^>]*>", "", text)
        text = re.sub(r"\n+", " ", text)
        text = re.sub(r"[0-9]", "", text)
        text = re.sub(r"[^\w\s]", " ", text)
        return text.strip()

    # -----------------------------
    # Преобразование POS для WordNet
    # -----------------------------
    def _map_pos(self, nltk_pos: str) -> str | None:
        if nltk_pos.startswith("N") and "NOUN" in self.keep_pos:
            return wordnet.NOUN
        if nltk_pos.startswith("V") and "VERB" in self.keep_pos:
            return wordnet.VERB
        if nltk_pos.startswith("J") and "ADJ" in self.keep_pos:
            return wordnet.ADJ
        return None

    # -----------------------------
    # Объединение MWEs и подсчёт частот
    # -----------------------------
    def _process_mwes(self, lemmas: list[str]) -> Tuple[List[str], Counter]:
        ordered = []
        freq_counter = Counter()
        i = 0
        n = len(lemmas)

        while i < n:
            matched = False
            for size in range(self.mwe_max, self.mwe_min - 1, -1):
                if i + size > n:
                    continue
                candidate = tuple(lemmas[i : i + size])
                if candidate in WORDNET_MWES:
                    phrase = " ".join(candidate)
                    ordered.append(phrase)
                    freq_counter[phrase] += 1
                    i += size
                    matched = True
                    break
            if not matched:
                word = lemmas[i]
                ordered.append(word)
                freq_counter[word] += 1
                i += 1
        return ordered, freq_counter

    # -----------------------------
    # Маппинг на существующие слова в базе
    # -----------------------------
    def _map_existing_words(self, word_counter: Counter) -> List[SubtitleWord]:
        subtitle_words = []

        names = [w for w in word_counter.keys() if w]  # безопасно убираем None/пустые
        if not names:
            return subtitle_words

        existing_words_qs = Word.objects.filter(name__in=names).prefetch_related(
            "word_parts__part_of_speech",
            "word_parts__translations",
        )

        for word in existing_words_qs:
            frequency = word_counter.get(word.name, 0)
            if frequency == 0:
                continue

            pos_objs = list(word.word_parts.all())
            if not pos_objs:
                continue

            pos_list = [wp.part_of_speech.name for wp in pos_objs]

            main_pos_obj = next(
                (p for p in pos_objs if getattr(p, "is_main", False)), None
            )
            if not main_pos_obj and pos_objs:
                main_pos_obj = pos_objs[0]
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
                selected_translation = (
                    translations_for_pos[selected_pos][0]
                    if translations_for_pos[selected_pos]
                    else ""
                )
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

    # -----------------------------
    # Сериализация для шаблона / preview
    # -----------------------------
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
