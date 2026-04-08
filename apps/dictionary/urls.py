from django.urls import path

from apps.dictionary import views

app_name = "dictionary"

urlpatterns = [
    path("dictionary/", views.dictionary_view, name="dictionary"),
    path("api/dictionary/", views.dictionary_api, name="dictionary_api"),
]
