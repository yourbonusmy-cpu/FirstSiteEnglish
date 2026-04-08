# apps/ingestion/routing.py
from django.urls import re_path
from .consumers import SaveProgressConsumer

websocket_urlpatterns = [
    re_path(r"^ws/save-progress/$", SaveProgressConsumer.as_asgi()),
]
