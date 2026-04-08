from django.contrib import admin

from apps.lists.models import UserSubtitleList, SubtitleList, SubtitleListWord


@admin.register(SubtitleList)
class SubtitleListAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "background_image",
        "is_public",
        "quantity_words",
        "modified_time",
    )
    list_filter = ("is_public", "owner", "is_hide")
    search_fields = ("name", "owner__username")
    readonly_fields = (
        "quantity_words",
        "quantity_words_frequencies",
        "quantity_learned_words",
        "quantity_learned_words_frequencies",
    )


@admin.register(UserSubtitleList)
class UserSubtitleListAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "user",
        "subtitle_list",
    )
    list_filter = ("user",)
