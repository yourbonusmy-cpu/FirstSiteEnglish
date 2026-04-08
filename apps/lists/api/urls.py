from rest_framework.routers import DefaultRouter
from .views import SubtitleListViewSet

router = DefaultRouter()
router.register(r"lists", SubtitleListViewSet, basename="lists")

urlpatterns = router.urls
