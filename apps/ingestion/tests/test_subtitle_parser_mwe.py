import os
from django.test import SimpleTestCase
from apps.ingestion.services.subtitle_word_service import SubtitleWordService


class SubtitleParserMWETest(SimpleTestCase):
    """
    Тест проверяет, что multi-word expressions (MWE)
    обрабатываются как единые слова без обращения к БД
    """

    def setUp(self):
        # путь к файлу fixtures
        self.file_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "subtitles", "mwe.srt"
        )
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.text = f.read()

        # ожидаемые MWE в файле
        self.expected_mwe = {
            "black chokeberry",
            "dogwood berry",
            "cape gooseberry",
            "alpine currant",
            "maqui berry",
        }

    def test_multi_word_expressions(self):
        # 1. Получаем данные через фасад без БД
        words_data = SubtitleWordService.process_text(self.text, map_to_db=False)

        # 2. Извлекаем имена слов
        parsed_words = {w["name"] for w in words_data}

        # 3. Проверяем, что MWE присутствуют как единое слово
        for mwe in self.expected_mwe:
            self.assertIn(mwe, parsed_words)
