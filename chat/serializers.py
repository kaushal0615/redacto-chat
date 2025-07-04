from ninja import Schema

class MessageSchema(Schema):
    room: str
    user: str
    content: str
    timestamp: str
