import re
from collections import Counter
from typing import List, Iterable

from apps.dictionary.models import Word
from apps.ingestion.services.nlp_loader_spacy import load_nlp


class SubtitleWord:
    def __init__(
        self,
        id: int,
        name: str,
        frequency: int,
        transcription: str = "",
        selected_pos: str = "",
        selected_translation: str = "",
        pos_list: list[str] | None = None,
        translations_for_pos: dict[str, list[str]] | None = None,
    ):
        self.id = id
        self.name = name
        self.frequency = frequency
        self.transcription = transcription
        self.selected_pos = selected_pos
        self.selected_translation = selected_translation
        self.pos_list = pos_list or []
        self.translations_for_pos = translations_for_pos or {}

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "transcription": self.transcription,
            "frequency": self.frequency,
            "pos_list": self.pos_list,
            "selected_pos": self.selected_pos,
            "translations_for_pos": self.translations_for_pos,
            "selected_translation": self.selected_translation,
        }


class ConvertTextToSubtitleWords:
    keep_pos = {"NOUN", "VERB", "ADJ"}
    min_len = 2
    chunk_size = 5000

    def __init__(self, text: str, task_id: str | None = None, redis_client=None):
        self.nlp = load_nlp()
        self.task_id = task_id
        self.redis_client = redis_client
        self.total_chunks = 0
        self.processed_chunks = 0

        self.subtitle_words: List[SubtitleWord] = self._convert(text)

    def _convert(self, text: str) -> List[SubtitleWord]:
        text = self._clean_text(text)
        counter = Counter()

        chunks = list(self._chunk_text(text))
        self.total_chunks = len(chunks)

        self._update_progress(0)

        for chunk in chunks:
            doc = self.nlp(chunk)

            for token in doc:
                if token.is_stop or token.is_punct or token.is_space:
                    continue

                lemma = token.lemma_.lower()

                if len(lemma) < self.min_len:
                    continue

                if token.pos_.upper() not in self.keep_pos and not (
                    token.pos_ == "PROPN" and token.tag_ in {"NN", "NNS"}
                ):
                    continue

                counter[lemma] += 1

            self.processed_chunks += 1
            self._update_progress()

        self._update_progress(95)

        result = self._map_existing_words(counter)

        self._update_progress(100)

        return result

    def _update_progress(self, forced_percent: int | None = None):
        if not self.redis_client or not self.task_id:
            return

        if forced_percent is not None:
            percent = forced_percent
        else:
            if self.total_chunks == 0:
                percent = 0
            else:
                percent = int(
                    (self.processed_chunks / self.total_chunks) * 90
                )  # до 90%, чтобы оставить место БД

        self.redis_client.set(
            f"subtitle:{self.task_id}:progress",
            percent,
        )

    def _clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"\d*:\d*:.*\n", "", text)
        text = re.sub(r"<[^>]*>", "", text)
        text = re.sub(r"[0-9]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _chunk_text(self, text: str) -> Iterable[str]:
        doc = self.nlp(text)
        buffer = []
        char_count = 0

        for sent in doc.sents:
            sent_text = sent.text.strip()
            if not sent_text:
                continue

            if char_count + len(sent_text) > self.chunk_size and buffer:
                yield " ".join(buffer)
                buffer = []
                char_count = 0

            buffer.append(sent_text)
            char_count += len(sent_text)

        if buffer:
            yield " ".join(buffer)

    def _map_existing_words(self, word_counter: Counter) -> List[SubtitleWord]:
        subtitle_words: List[SubtitleWord] = []

        if not word_counter:
            return subtitle_words

        existing_words_qs = Word.objects.filter(
            name__in=word_counter.keys()
        ).prefetch_related(
            "word_parts__part_of_speech",
            "word_parts__translations",
        )

        for word in existing_words_qs:
            freq = word_counter[word.name]
            pos_objs = list(word.word_parts.all())
            if not pos_objs:
                continue

            pos_list = [wp.part_of_speech.name for wp in pos_objs]

            main_pos_obj = next(
                (p for p in pos_objs if getattr(p, "is_main", False)), pos_objs[0]
            )
            selected_pos = main_pos_obj.part_of_speech.name

            translations_for_pos = {
                wp.part_of_speech.name: [t.translation for t in wp.translations.all()]
                for wp in pos_objs
            }

            main_translation_obj = main_pos_obj.translations.filter(
                is_main=True
            ).first()

            selected_translation = (
                main_translation_obj.translation
                if main_translation_obj
                else (
                    translations_for_pos[selected_pos][0]
                    if translations_for_pos[selected_pos]
                    else ""
                )
            )

            subtitle_words.append(
                SubtitleWord(
                    id=word.id,
                    name=word.name,
                    frequency=freq,
                    transcription=word.transcription,
                    selected_pos=selected_pos,
                    selected_translation=selected_translation,
                    pos_list=pos_list,
                    translations_for_pos=translations_for_pos,
                )
            )

        return subtitle_words

    def to_dict(self) -> List[dict]:
        return [w.to_dict() for w in self.subtitle_words]
