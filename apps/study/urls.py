from django.urls import path

from apps.study import views
from apps.study.views import (
    ToggleKnownWordView,
    KnownWordsView,
    UpdateWordStateView,
    KnownWordsAjaxView,
    DownloadKnownWordsView,
    UploadKnownWordsView,
)

app_name = "study"

urlpatterns = [
    path("finish/", views.finish_study, name="finish_study"),
    path("word-impression/", views.word_impression, name="word_impression"),
    path(
        "word/update-state/",
        UpdateWordStateView.as_view(),
        name="update_word_state",
    ),
    path(
        "study/<int:list_id>/mini-cards/", views.word_mini_cards, name="word_mini_cards"
    ),
    path("known-words/", KnownWordsView.as_view(), name="known_words"),
    path("known-words/ajax/", KnownWordsAjaxView.as_view(), name="known_words_ajax"),
    # скачать
    path(
        "known-words/download/",
        DownloadKnownWordsView.as_view(),
        name="download_known_words",
    ),
    # загрузить
    path(
        "known-words/upload/", UploadKnownWordsView.as_view(), name="upload_known_words"
    ),
    path("toggle-known-word/", ToggleKnownWordView.as_view(), name="toggle_known_word"),
    path("<int:list_id>/", views.study_words_view, name="study_cards"),
    path("<int:list_id>/easy/", views.study_easy_words_view, name="study_easy_cards"),
    path(
        "<int:list_id>/easy_2/",
        views.study_easy_2_words_view,
        name="study_easy_2_cards",
    ),
    path(
        "<int:list_id>/easy_3/",
        views.study_easy_3_words_view,
        name="study_easy_3_cards",
    ),
    path(
        "<int:list_id>/puzzle/",
        views.study_puzzle_words_view,
        name="study_puzzle_cards",
    ),
    path("submit-answer/", views.submit_answer, name="submit_answer"),
    path("<int:pk>/update-progress/", views.update_progress, name="update_progress"),
]
