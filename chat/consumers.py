# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Room, Message
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        #print(">>> Incoming message:", text_data)
        data = json.loads(text_data)

        try:
            user = await User.objects.aget(username=data["user"])
        except User.DoesNotExist:
            await self.send(text_data=json.dumps({"error": "User does not exist"}))
            return

        room, _ = await Room.objects.aget_or_create(name=data["room"])
        await Message.objects.acreate(user=user, room=room, content=data["content"])

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "user": data["user"],
                "message": data["content"],
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "user": event["user"],
            "message": event["message"]
        }))
