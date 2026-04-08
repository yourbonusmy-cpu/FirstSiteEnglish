from django.urls import path
from django.views.generic import TemplateView

from apps.ingestion.views import (
    SaveSubtitleListView,
    DeleteSubtitleWordView,
    SubtitleWordsPageView,
    get_subtitle_result,
    get_subtitle_progress,
    start_subtitle_processing,
    cache_subtitle_result,
    SubtitlePreviewView,
)

app_name = "ingestion"

urlpatterns = [
    path("subtitle/cache-result/", cache_subtitle_result, name="subtitle_cache_result"),
    path("subtitle/start/", start_subtitle_processing, name="subtitle_start"),
    path("subtitle/progress/", get_subtitle_progress, name="subtitle_progress"),
    path("subtitle/result/", get_subtitle_result, name="subtitle_result"),
    path("subtitle/preview/", SubtitlePreviewView.as_view(), name="subtitle_preview"),
    path("subtitle/page/", SubtitleWordsPageView.as_view(), name="subtitle_page"),
    path("subtitle/save/", SaveSubtitleListView.as_view(), name="subtitle_save"),
    path(
        "subtitle/delete-word/",
        DeleteSubtitleWordView.as_view(),
        name="subtitle_delete_word",
    ),
    path(
        "subtitle/add/",
        TemplateView.as_view(template_name="ingestion/subtitle_add_fix.html"),
        name="subtitle_add",
    ),
]
