import spacy
from threading import Lock
from pathlib import Path

from .phrasal_extractor import PhrasalExtractor

_LOCK = Lock()

_NLP = None
_PV_EXTRACTOR = None


def get_nlp():
    global _NLP
    if _NLP is None:
        with _LOCK:
            if _NLP is None:
                _NLP = spacy.load(
                    "en_core_web_sm",
                    disable=[
                        "ner",
                        "parser",
                        "textcat",
                        "sentencizer",
                        "attribute_ruler",
                    ],
                )
    return _NLP


def get_phrasal_extractor():
    global _PV_EXTRACTOR
    if _PV_EXTRACTOR is None:
        with _LOCK:
            if _PV_EXTRACTOR is None:
                pv_path = (
                    Path(__file__).resolve().parent
                    / "fixtures"
                    / "phrasal_verbs_cleaned_640.txt"
                )
                _PV_EXTRACTOR = PhrasalVerbExtractor(
                    pv_path=str(pv_path),
                    nlp=get_nlp(),
                )
    return _PV_EXTRACTOR
