from django.db import models


class Word(models.Model):
    name = models.CharField(
        max_length=64, unique=True, db_index=True, null=True, blank=True
    )
    transcription = models.CharField(max_length=64, blank=True, default="")

    def __str__(self):
        return self.name

    class Meta:
        db_table = "dictionary_words"


class PartOfSpeech(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = "dictionary_part_of_speech"

    def __str__(self):
        return self.name


class WordPartOfSpeech(models.Model):
    word = models.ForeignKey(
        "dictionary.Word",
        on_delete=models.CASCADE,
        related_name="word_parts",
    )

    part_of_speech = models.ForeignKey(
        "dictionary.PartOfSpeech",
        on_delete=models.PROTECT,
        related_name="word_links",
    )

    is_main = models.BooleanField(default=False)

    class Meta:
        db_table = "dictionary_word_parts"
        unique_together = ("word", "part_of_speech")


class Translation(models.Model):
    translation = models.CharField(max_length=128, blank=True, default="")
    is_main = models.BooleanField(default=False)

    word_part_of_speech = models.ForeignKey(
        "dictionary.WordPartOfSpeech",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="translations",
    )

    def __str__(self):
        return self.translation

    class Meta:
        db_table = "dictionary_translations"
