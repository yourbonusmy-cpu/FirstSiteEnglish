from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

app_name = "lists"


urlpatterns = [
    path("", views.public_lists, name="public_lists"),
    path("test", views.gradient_text, name="gradient_text"),
    path("my-lists/", views.my_lists, name="my_lists"),
    path("lists/<int:list_id>/delete/", views.delete_list, name="delete_list"),
    path("lists/edit/<int:list_id>/", views.word_list_edit, name="word_list_edit"),
    path("lists/<int:list_id>/", views.word_list_detail, name="word_list_detail"),
    path(
        "translations/<word_id>/?part=<part_id>",
        views.get_translations,
        name="get_translations",
    ),
    path("lists/<int:pk>/toggle-publish/", views.toggle_publish, name="toggle_publish"),
    path("lists/<int:list_id>/download/", views.download_words, name="download_words"),
    path("about/", views.about, name="about"),
    path("my-react/", views.my_lists_react, name="my_lists_react"),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
