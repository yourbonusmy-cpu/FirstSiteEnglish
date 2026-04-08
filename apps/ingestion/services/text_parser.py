import re
from collections import Counter
from typing import Iterable
from apps.ingestion.services.nlp_loader_nltk import load_nlp


class TextParser:
    keep_pos = {"NOUN", "VERB", "ADJ"}
    min_len = 2
    chunk_size = 20_000

    def __init__(self, text: str):
        self._raw_text = text
        self.nlp = load_nlp()

    def clean_text(self) -> str:
        text = self._raw_text.lower()
        text = re.sub(r"\d*:\d*:.*\n", "", text)
        text = re.sub(r"<[^>]*>", "", text)
        text = re.sub(r"\n+", " ", text)
        text = re.sub(r"[0-9]", "", text)
        text = re.sub(r"[^\w\s]", " ", text)
        return text.strip()

    def _chunk_text(self, text: str) -> Iterable[str]:
        for i in range(0, len(text), self.chunk_size):
            yield text[i : i + self.chunk_size]

    def _extract_noun_phrases(self, doc) -> Counter:
        phrases = Counter()
        for chunk in doc.noun_chunks:
            if chunk.root.pos_ != "NOUN" or len(chunk) < 2:
                continue
            tokens = []
            valid = True
            for token in chunk:
                if token.is_stop or token.pos_ not in {"ADJ", "NOUN", "PROPN"}:
                    valid = False
                    break
                tokens.append(token.lemma_.lower())
            if valid:
                phrases[" ".join(tokens)] += 1
        return phrases

    def _get_phrase_token_indexes(self, doc) -> set[int]:
        used = set()
        for chunk in doc.noun_chunks:
            if chunk.root.pos_ != "NOUN" or len(chunk) < 2:
                continue
            for token in chunk:
                used.add(token.i)
        return used

    def get_frequencies(self) -> Counter:
        text = self.clean_text()
        counter = Counter()
        for doc in self.nlp.pipe(self._chunk_text(text), batch_size=32):
            # noun phrases
            phrase_counter = self._extract_noun_phrases(doc)
            counter.update(phrase_counter)
            phrase_token_ids = self._get_phrase_token_indexes(doc)
            # single words
            for token in doc:
                if (
                    token.i in phrase_token_ids
                    or token.is_stop
                    or token.is_punct
                    or token.is_space
                ):
                    continue
                if token.pos_.upper() not in self.keep_pos:
                    continue
                lemma = token.lemma_.lower()
                if len(lemma) < self.min_len:
                    continue
                counter[lemma] += 1
        return counter
