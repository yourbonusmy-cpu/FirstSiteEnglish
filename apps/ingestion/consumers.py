# apps/ingestion/consumers.py


import json
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer


class SaveProgressConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        # 🔥 ВАЖНО
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.group_name = f"user_{user.id}"

        # 🔥 ПОДПИСКА НА ТУ ЖЕ ГРУППУ
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        print(f"[WS] Connected to {self.group_name}")  # 👈 лог

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"[WS] Disconnected from {self.group_name}")

    async def ingestion_event(self, event):
        print("[WS] EVENT:", event)  # 👈 лог

        await self.send(text_data=json.dumps(event["data"]))


class IngestionConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.group_name = f"user_{self.scope['user'].id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def ingestion_event(self, event):
        await self.send_json(event["data"])