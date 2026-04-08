# apps/ingestion/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class SaveProgressConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        # <-- должно совпадать с тем, что в tasks.py
        self.group_name = f"user_{self.scope['user'].id}"  # было save_user_{id}
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def save_progress(self, event):
        print("WS EVENT:", event)
        # тип события должен совпадать с 'type' из send_ws
        await self.send_json(event["data"])
