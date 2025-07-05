from ninja import Schema
from typing import Optional , List
from datetime import datetime

class GroupMessageSchema(Schema):
    group: str
    author: str
    body: Optional[str]
    file_url: Optional[str]
    created: datetime

class ChatGroupSchema(Schema):
    group_name: str
    groupchat_name: Optional[str]
    is_private: bool
    members: list[str]

class ChatGroupCreateSchema(Schema):
    groupchat_name: Optional[str]
    is_private: bool
    members: List[str]