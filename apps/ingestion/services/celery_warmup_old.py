# apps/ingestion/celery_warmup.py

from celery.signals import worker_ready


@worker_ready.connect
def warmup_nlp(**kwargs):
    # NLTK
    from apps.ingestion.services.nlp_loader_nltk import (
        get_lemmatizer,
        get_stop_words,
    )

    get_lemmatizer()
    get_stop_words()

    # spaCy
    from apps.ingestion.services.nlp_loader_spacy import load_nlp_spacy

    load_nlp_spacy()

    print("🔥 NLP warm-up completed")
