from django.core.management.base import BaseCommand
from django.db import transaction

from apps.dictionary.models import (
    Word,
    PartOfSpeech,
    WordPartOfSpeech,
    Translation,
)

PHRASAL_VERB_POS_ID = 22  # фиксированно по условию


class Command(BaseCommand):
    help = "Import phrasal verbs from phrasal_verbs_merged.txt"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            required=True,
            help="Path to phrasal_verbs_merged.txt",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = options["path"]

        pos = PartOfSpeech.objects.get(id=PHRASAL_VERB_POS_ID)

        created_words = 0

        with open(path, "r", encoding="utf-8") as f:
            for line_num, raw_line in enumerate(f, 1):
                line = raw_line.strip()
                if not line:
                    continue

                try:
                    name, transcription, translations_raw = line.split("|")
                except ValueError:
                    self.stderr.write(f"[line {line_num}] invalid format: {line}")
                    continue

                name = name.strip()
                transcription = transcription.strip()
                translations_raw = translations_raw.strip()

                # --- Word ---
                word, word_created = Word.objects.get_or_create(
                    name=name,
                    defaults={"transcription": transcription},
                )

                if not word_created and transcription and not word.transcription:
                    word.transcription = transcription
                    word.save(update_fields=["transcription"])

                # --- WordPartOfSpeech ---
                wpos, _ = WordPartOfSpeech.objects.get_or_create(
                    word=word,
                    part_of_speech=pos,
                    defaults={"is_main": True},
                )

                # --- Translations ---
                Translation.objects.filter(word_part_of_speech=wpos).delete()

                translations = [
                    t.strip()
                    for t in translations_raw.replace(";", ",").split(",")
                    if t.strip()
                ]

                for i, tr in enumerate(translations):
                    Translation.objects.create(
                        translation=tr,
                        is_main=(i == 0),
                        word_part_of_speech=wpos,
                    )

                created_words += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {created_words} phrasal verbs"))
