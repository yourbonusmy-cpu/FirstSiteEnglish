import os

from django.apps import AppConfig


class IngestionConfig(AppConfig):
    name = "apps.ingestion"
    #
    # def ready(self):
    #     if os.environ.get("RUN_MAIN") == "true":
    #         if True:
    #             load_nlp_spacy()
    #         if True:
    #             initialize_nltk_resources()
