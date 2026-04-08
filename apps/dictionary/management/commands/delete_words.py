from django.core.management.base import BaseCommand
from apps.dictionary.models import Word


class Command(BaseCommand):
    help = "Удаляет слова из списка из базы данных"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str,
            help="Путь к файлу со словами, каждое слово с новой строки",
        )

    def handle(self, *args, **options):
        file_path = options["file_path"]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                words_list = [line.strip() for line in f if line.strip()]

            total_deleted_words = 0
            total_deleted_all = 0
            chunk_size = 500

            for i in range(0, len(words_list), chunk_size):
                chunk = words_list[i : i + chunk_size]
                deleted_total, deleted_per_model = Word.objects.filter(
                    name__in=chunk
                ).delete()
                total_deleted_all += deleted_total
                total_deleted_words += deleted_per_model.get("dictionary_words", 0)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Удалено слов из Word: {total_deleted_words}\n"
                    f"Общее количество удалённых записей (включая CASCADE): {total_deleted_all}"
                )
            )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Файл {file_path} не найден."))
