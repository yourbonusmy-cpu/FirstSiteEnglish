from apps.dictionary.models import Word
from apps.ingestion.services.subtitle_parser import SubtitleWord


class SubtitleWordMapper:
    """
    Маппинг Counter слов в объекты SubtitleWord с базой
    """

    @staticmethod
    def map_counter_to_subtitle_words(counter) -> list[SubtitleWord]:
        subtitle_words = []
        if not counter:
            return subtitle_words

        existing_words_qs = Word.objects.filter(
            name__in=counter.keys()
        ).prefetch_related("word_parts__part_of_speech", "word_parts__translations")

        for word in existing_words_qs:
            freq = counter.get(word.name, 0)
            if freq == 0:
                continue

            pos_objs = list(word.word_parts.all())
            if not pos_objs:
                continue

            pos_list = [wp.part_of_speech.name for wp in pos_objs]
            main_pos_obj = next(
                (p for p in pos_objs if getattr(p, "is_main", False)), pos_objs[0]
            )
            selected_pos = main_pos_obj.part_of_speech.name
            translations_for_pos = {
                wp.part_of_speech.name: [t.translation for t in wp.translations.all()]
                for wp in pos_objs
            }
            main_translation_obj = main_pos_obj.translations.filter(
                is_main=True
            ).first()
            selected_translation = (
                main_translation_obj.translation
                if main_translation_obj
                else (
                    translations_for_pos[selected_pos][0]
                    if translations_for_pos[selected_pos]
                    else ""
                )
            )

            subtitle_words.append(
                SubtitleWord(
                    name=word.name,
                    frequency=freq,
                    transcription=word.transcription,
                    selected_pos=selected_pos,
                    selected_translation=selected_translation,
                    pos_list=pos_list,
                    translations_for_pos=translations_for_pos,
                )
            )

        return subtitle_words
