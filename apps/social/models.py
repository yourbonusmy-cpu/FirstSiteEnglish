from django.db import models
from django.conf import settings

from apps.lists.models import SubtitleList


class SubtitleListLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subtitle_list_likes",
    )
    subtitle_list = models.ForeignKey(
        "lists.SubtitleList", on_delete=models.CASCADE, related_name="likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "lists_userslistslikes"
        unique_together = ("user", "subtitle_list")
