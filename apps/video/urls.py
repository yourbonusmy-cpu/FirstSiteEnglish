from django.urls import path

from apps.video import views

app_name = "video"


urlpatterns = [
    path("video/<str:filename>", views.stream_video, name="stream-video"),
    path("video-test/", views.video_test, name="video-test"),
    path("test/", views.video_player, name="video-player"),
    # path("youtube/", views.youtube_download, name="youtube_download"),
    # path(
    #     "youtube/download/", views.youtube_download_file, name="youtube_download_file"
    # ),
]
