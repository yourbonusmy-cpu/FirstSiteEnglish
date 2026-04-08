# Запуск
# python manage.py startapp migration_tools

from django.core.management.base import BaseCommand
from django.db import connections, transaction
from apps.dictionary.models import Word, PartOfSpeech, WordPartOfSpeech, Translation


class Command(BaseCommand):
    help = "Import parsed database into Django database"

    def handle(self, *args, **kwargs):
        parsed_conn = connections["parsed"]

        # 1️⃣ Получаем все слова из парсенной базы
        with parsed_conn.cursor() as cursor:
            cursor.execute("SELECT id, name, transcription FROM dictionary_words")
            words_rows = cursor.fetchall()

            cursor.execute("SELECT id, name FROM dictionary_part_of_speech")
            pos_rows = cursor.fetchall()

            cursor.execute("""
                SELECT id, word_id, part_of_speech_id, is_main
                FROM dictionary_word_parts
            """)
            word_parts_rows = cursor.fetchall()

            cursor.execute("""
                SELECT id, word_part_of_speech_id, translation, is_main
                FROM dictionary_translations
            """)
            translations_rows = cursor.fetchall()

        # 2️⃣ Импортируем PartOfSpeech
        pos_map = {}
        for pos_id, name in pos_rows:
            obj, _ = PartOfSpeech.objects.get_or_create(name=name)
            pos_map[pos_id] = obj

        # 3️⃣ Импортируем Word
        word_map = {}
        for word_id, name, transcription in words_rows:
            obj, _ = Word.objects.get_or_create(
                name=name, defaults={"transcription": transcription}
            )
            word_map[word_id] = obj

        # 4️⃣ Импортируем WordPartOfSpeech
        wp_map = {}
        for wp_id, word_id, pos_id, is_main in word_parts_rows:
            word_obj = word_map[word_id]
            pos_obj = pos_map[pos_id]

            wp_obj, _ = WordPartOfSpeech.objects.get_or_create(
                word=word_obj, part_of_speech=pos_obj, defaults={"is_main": is_main}
            )
            wp_map[wp_id] = wp_obj

        # 5️⃣ Импортируем Translations
        objs = []
        for t_id, wp_id, translation_text, is_main in translations_rows:
            wp_obj = wp_map[wp_id]
            objs.append(
                Translation(
                    word_part_of_speech=wp_obj,
                    translation=translation_text,
                    is_main=is_main,
                )
            )

        # создаём батчами и игнорируем конфликты
        Translation.objects.bulk_create(objs, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS("Импорт завершён!"))
