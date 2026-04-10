# apps/ingestion/routing.py
from django.urls import re_path
from .consumers import IngestionConsumer, SaveProgressConsumer

websocket_urlpatterns = [
    re_path(r"^ws/ingestion/$", IngestionConsumer.as_asgi()),
    re_path(r"ws/save-progress/$", SaveProgressConsumer.as_asgi()),
]