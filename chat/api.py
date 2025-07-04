from ninja import NinjaAPI
from .models import Message
from .serializers import MessageSchema

api = NinjaAPI()

@api.get("/rooms/{room_name}/messages", response=list[MessageSchema])
def get_messages(request, room_name: str):
    messages = Message.objects.filter(room__name=room_name).select_related("user")
    return [
        MessageSchema(
            room=room_name,
            user=msg.user.username,
            content=msg.content,
            timestamp=str(msg.timestamp)
        ) for msg in messages
    ]
