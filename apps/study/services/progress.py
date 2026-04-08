# lists/services/progress.py
from django.db.models import Count

from apps.lists.models import UserSubtitleList
from apps.study.models import UserWordProgress


def update_subtitle_list_progress(user, subtitle_list):
    learned_word_ids = (
        UserWordProgress.objects.filter(
            user=user,
            is_learned=True,
            word__subtitle_links__subtitle_list=subtitle_list,
        )
        .values_list("word_id", flat=True)
        .distinct()
    )

    learned_count = learned_word_ids.count()

    user_list, _ = UserSubtitleList.objects.get_or_create(
        user=user,
        subtitle_list=subtitle_list,
    )

    user_list.quantity_learned_words = learned_count
    user_list.save(update_fields=["quantity_learned_words"])

    return learned_count
