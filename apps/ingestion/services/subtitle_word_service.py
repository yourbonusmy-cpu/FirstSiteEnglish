from apps.ingestion.services.text_parser import TextParser
from apps.ingestion.services.subtitle_word_mapper import SubtitleWordMapper
from apps.ingestion.services.subtitle_word_presenter import SubtitleWordPresenter


class SubtitleWordService:
    """
    Фасад для получения слов и MWE сразу для шаблона
    """

    @staticmethod
    def process_text(text: str, map_to_db: bool = True) -> list[dict]:
        # 1. Парсинг текста
        parser = TextParser(text)
        counter = parser.get_frequencies()

        if map_to_db:
            # 2. Проверка в базе и создание SubtitleWord
            subtitle_words = SubtitleWordMapper.map_counter_to_subtitle_words(counter)
        else:
            # Для теста без БД – создаём временные SubtitleWord только с частотой
            from apps.ingestion.services.subtitle_parser import SubtitleWord

            subtitle_words = [
                SubtitleWord(name=k, frequency=v) for k, v in counter.items()
            ]

        # 3. Подготовка для шаблона/JSON
        return SubtitleWordPresenter.to_dict(subtitle_words)
