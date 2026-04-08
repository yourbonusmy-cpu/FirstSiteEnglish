from celery.signals import worker_ready


@worker_ready.connect
def warmup_nlp(**kwargs):
    from .nlp_loader_spacy import get_nlp, get_phrasal_extractor

    get_nlp()
    get_phrasal_extractor()

    print("✅ spaCy + PhrasalVerbExtractor warmed up")
