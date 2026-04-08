# config/routing.py
from apps.social.routing import websocket_urlpatterns as social_ws
from apps.ingestion.routing import websocket_urlpatterns as ingestion_ws

websocket_urlpatterns = social_ws + ingestion_ws
