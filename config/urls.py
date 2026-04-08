from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from config import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.lists.urls")),
    path("api/", include("apps.lists.api.urls")),
    path("dictionary/", include("apps.dictionary.urls")),
    path("study/", include("apps.study.urls")),
    path("social/", include("apps.social.urls")),
    path("ingestion/", include("apps.ingestion.urls")),
    path("video/", include("apps.video.urls")),
    path("accounts/", include("apps.accounts.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
