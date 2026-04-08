from apps.ingestion.services.subtitle_parser import SubtitleWord


class SubtitleWordPresenter:
    """
    Преобразует SubtitleWord в словарь/JSON для шаблона
    """

    @staticmethod
    def to_dict(subtitle_words: list[SubtitleWord]) -> list[dict]:
        return [
            {
                "name": w.name,
                "transcription": w.transcription,
                "frequency": w.frequency,
                "pos_list": w.pos_list,
                "selected_pos": w.selected_pos,
                "translations_for_pos": w.translations_for_pos,
                "selected_translation": w.selected_translation,
            }
            for w in subtitle_words
        ]
