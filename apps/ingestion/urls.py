from django.urls import path
from apps.ingestion import views

app_name = "ingestion"

# ingestion/urls.py
from django.urls import path
from . import views

app_name = "ingestion"

urlpatterns = [
    # Страница добавления субтитров
    path("subtitle/add/", views.SubtitleAddView.as_view(), name="subtitle_add"),

    # Загрузка текста/файла → запуск Celery
    path("subtitle/start/", views.SubtitleStartView.as_view(), name="subtitle_start"),

    # Прогресс обработки субтитров
    path("subtitle/progress/", views.SubtitleProgressView.as_view(), name="subtitle_progress"),

    # Пагинация preview
    path("subtitle/page/", views.SubtitlePageView.as_view(), name="subtitle_page"),

    # Удаление слова из preview
    path("subtitle/delete_word/", views.SubtitleDeleteWordView.as_view(), name="subtitle_delete_word"),

    # Сохранение списка субтитров
    path("subtitle/save/", views.SubtitleSaveView.as_view(), name="subtitle_save"),

    # Прогресс сохранения
    path("subtitle/save_progress/", views.SubtitleSaveProgressView.as_view(), name="subtitle_save_progress"),

    # Отмена сохранения
    path("subtitle/save_cancel/", views.SubtitleSaveCancelView.as_view(), name="subtitle_save_cancel"),
]