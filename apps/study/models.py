from django.db import models
from django.conf import settings


class UserWordProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="word_progress"
    )
    word = models.ForeignKey(
        "dictionary.Word", on_delete=models.CASCADE, related_name="progress_by_users"
    )
    is_learning = models.BooleanField(default=False)
    is_learned = models.BooleanField(default=False)
    impressions = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    level_learned = models.IntegerField(default=0)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    stability_days = models.IntegerField(default=0)

    # Новые поля
    is_hard = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "study_userwordprogress"
        unique_together = ("user", "word")

        indexes = [
            # 1️⃣ Быстрый доступ к прогрессу слова
            models.Index(
                fields=["user", "word"],
                name="idx_uwp_user_word",
            ),
            # 2️⃣ Для подбора слов на повторение
            models.Index(
                fields=["user", "is_learned", "last_reviewed_at"],
                name="idx_uwp_review_queue",
            ),
        ]
