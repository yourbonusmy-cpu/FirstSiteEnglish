import re
from collections import Counter
from typing import Iterable, List

from apps.dictionary.models import Word
from apps.ingestion.services.nlp_loader_nltk import load_nlp

# =========================
# DTO
# =========================


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


# =========================
# Main parser
# =========================


class ConvertTextToSubtitleWords:
    keep_pos = {"NOUN", "VERB", "ADJ"}
    min_len = 2
    chunk_size = 20_000

    def __init__(self, text: str):
        self._raw_text = text
        self.nlp = load_nlp()
        self.subtitle_words: List[SubtitleWord] = self._convert(text)

    # =========================
    # Pipeline
    # =========================

    def get_frequencies(self) -> Counter:
        """
        Возвращает частоты слов и фраз
        БЕЗ обращения к базе данных
        """
        text = self._clean_text(self._raw_text)
        return self._get_word_frequencies(text)

    def _convert(self, text: str) -> List[SubtitleWord]:
        text = self._clean_text(text)
        word_counter = self._get_word_frequencies(text)
        return self._map_existing_words(word_counter)

    # =========================
    # Text cleaning
    # =========================

    def _clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"\d*:\d*:.*\n", "", text)
        text = re.sub(r"<[^>]*>", "", text)
        text = re.sub(r"\n+", " ", text)
        text = re.sub(r"[0-9]", "", text)
        text = re.sub(r"[^\w\s]", " ", text)
        return text.strip()

    # =========================
    # Chunking
    # =========================

    def _chunk_text(self, text: str) -> Iterable[str]:
        for i in range(0, len(text), self.chunk_size):
            yield text[i : i + self.chunk_size]

    # =========================
    # Phrase extraction
    # =========================

    def _extract_noun_phrases(self, doc) -> Counter:
        """
        Автоматическое извлечение noun phrases:
        - минимум 2 слова
        - root = NOUN
        - только ADJ / NOUN / PROPN
        - без stop-слов
        """
        phrases = Counter()

        for chunk in doc.noun_chunks:
            if chunk.root.pos_ != "NOUN":
                continue

            if len(chunk) < 2:
                continue

            tokens = []
            valid = True

            for token in chunk:
                if token.is_stop:
                    valid = False
                    break

                if token.pos_ not in {"ADJ", "NOUN", "PROPN"}:
                    valid = False
                    break

                tokens.append(token.lemma_.lower())

            if not valid:
                continue

            phrase = " ".join(tokens)
            phrases[phrase] += 1

        return phrases

    def _get_phrase_token_indexes(self, doc) -> set[int]:
        """
        Индексы токенов, входящих в noun phrases,
        чтобы не учитывать их повторно как одиночные слова
        """
        used = set()

        for chunk in doc.noun_chunks:
            if chunk.root.pos_ != "NOUN":
                continue

            if len(chunk) < 2:
                continue

            for token in chunk:
                used.add(token.i)

        return used

    # =========================
    # Frequency calculation
    # =========================

    def _get_word_frequencies(self, text: str) -> Counter:
        counter = Counter()

        for doc in self.nlp.pipe(self._chunk_text(text), batch_size=32):

            # 1. noun phrases
            phrase_counter = self._extract_noun_phrases(doc)
            counter.update(phrase_counter)

            # 2. mask phrase tokens
            phrase_token_ids = self._get_phrase_token_indexes(doc)

            # 3. single words
            for token in doc:
                if token.i in phrase_token_ids:
                    continue

                if token.is_stop or token.is_space or token.is_punct:
                    continue

                if token.pos_.upper() not in self.keep_pos:
                    continue

                lemma = token.lemma_.lower()
                if len(lemma) < self.min_len:
                    continue

                counter[lemma] += 1

        return counter

    # =========================
    # DB mapping
    # =========================

    def _map_existing_words(self, word_counter: Counter) -> List[SubtitleWord]:
        subtitle_words = []

        if not word_counter:
            return subtitle_words

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
            if not pos_objs:
                continue

            pos_list = [wp.part_of_speech.name for wp in pos_objs]

            main_pos_obj = next(
                (p for p in pos_objs if getattr(p, "is_main", False)),
                pos_objs[0],
            )

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
            else:
                selected_translation = (
                    translations_for_pos[selected_pos][0]
                    if translations_for_pos[selected_pos]
                    else ""
                )

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

    # =========================
    # Serialization
    # =========================

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
