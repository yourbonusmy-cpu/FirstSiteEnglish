from django.db import models


class OldWord(models.Model):
    name = models.CharField(max_length=128)
    transcription = models.CharField(max_length=128, blank=True)

    class Meta:
        db_table = "lists_word"
        managed = False
        app_label = "dictionary"


class OldPartOfSpeech(models.Model):
    name = models.CharField(max_length=128)
    is_main = models.BooleanField(default=False)
    word = models.ForeignKey(
        OldWord,
        on_delete=models.DO_NOTHING,
        db_column="word_id",
    )

    class Meta:
        db_table = "lists_pathofspeech"
        managed = False
        app_label = "dictionary"


class OldTranslation(models.Model):
    translation = models.CharField(max_length=255)
    is_main = models.BooleanField(default=False)
    path_of_speech = models.ForeignKey(
        OldPartOfSpeech,
        on_delete=models.DO_NOTHING,
        db_column="path_of_speech_id",
        null=True,
    )

    class Meta:
        db_table = "lists_translation"
        managed = False
        app_label = "dictionary"
