# apps/ingestion/services/nlp_loader_nltk.py

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

LEMMATIZER = None
STOP_WORDS = None


def get_lemmatizer() -> WordNetLemmatizer:
    global LEMMATIZER
    if LEMMATIZER is None:
        LEMMATIZER = WordNetLemmatizer()
    return LEMMATIZER


def get_stop_words() -> set[str]:
    global STOP_WORDS
    if STOP_WORDS is None:
        STOP_WORDS = set(stopwords.words("english"))
    return STOP_WORDS
