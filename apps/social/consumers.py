import json
from channels.generic.websocket import (
    AsyncWebsocketConsumer,
)


class LikesConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_name = "likes_updates"

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def like_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "list_id": event["list_id"],
                    "likes_count": event["likes_count"],
                }
            )
        )
