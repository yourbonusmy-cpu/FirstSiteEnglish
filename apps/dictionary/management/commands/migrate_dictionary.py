from django.core.management.base import BaseCommand
from django.db import transaction, connections

from apps.dictionary.legacy_models import (
    OldWord,
    OldPartOfSpeech,
    OldTranslation,
)
from apps.dictionary.models import (
    Word,
    WordPartOfSpeech,
    Translation,
)

BATCH = 1000


class Command(BaseCommand):
    help = "Fast migration from SQLite to PostgreSQL"

    def handle(self, *args, **options):
        self.stdout.write("Fast migration started")

        with transaction.atomic(using="default"):
            self.migrate_words()
            self.migrate_pos()
            self.migrate_translations()
            self.fix_sequences()

        self.stdout.write(self.style.SUCCESS("Migration completed"))

    # ------------------------

    def migrate_words(self):
        qs = OldWord.objects.using("old_sqlite").all()
        total = qs.count()

        objs = []
        for i, w in enumerate(qs.iterator(chunk_size=BATCH), 1):
            objs.append(
                Word(
                    id=w.id,  # 👈 сохраняем ID
                    name=w.name,
                    transcription=w.transcription,
                )
            )

            if len(objs) == BATCH:
                Word.objects.bulk_create(objs)
                objs.clear()

        if objs:
            Word.objects.bulk_create(objs)

        self.stdout.write(f"Words migrated: {total}")

    # ------------------------

    def migrate_pos(self):
        qs = OldPartOfSpeech.objects.using("old_sqlite").all()
        total = qs.count()

        objs = []
        for pos in qs.iterator(chunk_size=BATCH):
            objs.append(
                WordPartOfSpeech(
                    id=pos.id,
                    name=pos.name,
                    is_main=pos.is_main,
                    word_id=pos.word_id,  # 👈 FK напрямую
                )
            )

            if len(objs) == BATCH:
                WordPartOfSpeech.objects.bulk_create(objs)
                objs.clear()

        if objs:
            WordPartOfSpeech.objects.bulk_create(objs)

        self.stdout.write(f"PartOfSpeech migrated: {total}")

    # ------------------------

    def migrate_translations(self):
        qs = OldTranslation.objects.using("old_sqlite").all()
        total = qs.count()

        objs = []
        for tr in qs.iterator(chunk_size=BATCH):
            objs.append(
                Translation(
                    id=tr.id,
                    translation=tr.translation,
                    is_main=tr.is_main,
                    part_of_speech_id=tr.path_of_speech_id,
                )
            )

            if len(objs) == BATCH:
                Translation.objects.bulk_create(objs)
                objs.clear()

        if objs:
            Translation.objects.bulk_create(objs)

        self.stdout.write(f"Translations migrated: {total}")

    # ------------------------

    def fix_sequences(self):
        """PostgreSQL sequence fix"""
        with connections["default"].cursor() as cursor:
            cursor.execute("""
                SELECT setval(
                    pg_get_serial_sequence('dictionary_words', 'id'),
                    COALESCE(MAX(id), 1)
                ) FROM dictionary_words;
            """)
            cursor.execute("""
                SELECT setval(
                    pg_get_serial_sequence('dictionary_parts_of_speech', 'id'),
                    COALESCE(MAX(id), 1)
                ) FROM dictionary_parts_of_speech;
            """)
            cursor.execute("""
                SELECT setval(
                    pg_get_serial_sequence('dictionary_translations', 'id'),
                    COALESCE(MAX(id), 1)
                ) FROM dictionary_translations;
            """)

        self.stdout.write("PostgreSQL sequences fixed")
