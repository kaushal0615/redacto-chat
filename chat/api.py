from ninja import NinjaAPI, File
from ninja.files import UploadedFile
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import ChatGroup, GroupMessage
from .serializers import GroupMessageSchema, ChatGroupSchema, ChatGroupCreateSchema

from ninja.security import django_auth

api = NinjaAPI(auth=django_auth)


@api.get("/groups", response=list[ChatGroupSchema])
def list_groups(request):
    groups = ChatGroup.objects.prefetch_related("members").all()
    return [
        ChatGroupSchema(
            group_name=g.group_name,
            groupchat_name=g.groupchat_name,
            is_private=g.is_private,
            members=[u.username for u in g.members.all()]
        )
        for g in groups
    ]

@api.get("/groups/{groupchat_name}/messages", response=list[GroupMessageSchema])
def get_group_messages(request, groupchat_name: str):
    group = get_object_or_404(ChatGroup, groupchat_name=groupchat_name)
    messages = GroupMessage.objects.filter(group=group).select_related("author")
    return [
        GroupMessageSchema(
            group=group.group_name,
            author=msg.author.username,
            body=msg.body,
            file_url=msg.file.url if msg.file else None,
            created=msg.created,
        ) for msg in messages
    ]

@api.post("/groups/{groupchat_name}/messages", response=GroupMessageSchema)
def post_message(request, groupchat_name: str, body: str):
    group = get_object_or_404(ChatGroup, groupchat_name=groupchat_name)
    user = request.user
    msg = GroupMessage.objects.create(group=group, author=user, body=body)
    return GroupMessageSchema(
        group=group.group_name,
        author=user.username,
        body=msg.body,
        file_url=None,
        created=msg.created,
    )

@api.post("/groups/{groupchat_name}/upload", response=GroupMessageSchema)
def upload_file(request, groupchat_name: str, file: UploadedFile = File(...)):
    group = get_object_or_404(ChatGroup, groupchat_name=groupchat_name)
    user = request.user
    msg = GroupMessage.objects.create(group=group, author=user, file=file)
    return GroupMessageSchema(
        group=group.group_name,
        author=user.username,
        body=None,
        file_url=msg.file.url,
        created=msg.created,
    )

@api.post("/groups", response=ChatGroupSchema)
def create_group(request, data: ChatGroupCreateSchema):
    group = ChatGroup.objects.create(
        groupchat_name=data.groupchat_name,
        is_private=data.is_private,
    )
    for username in data.members:
        user = get_object_or_404(User, username=username)
        group.members.add(user)
    group.save()
    return ChatGroupSchema(
        group_name=group.group_name,
        groupchat_name=group.groupchat_name,
        is_private=group.is_private,
        members=[u.username for u in group.members.all()],
    )