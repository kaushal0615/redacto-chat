# chat/consumers.py
import json
from channels.generic.websocket import WebsocketConsumer
from .models import ChatGroup, GroupMessage
from django.contrib.auth.models import User
from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404

class ChatroomConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name']
        self.chatroom = get_object_or_404(ChatGroup, group_name=self.chatroom_name)

        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name, self.channel_name
        )

        if self.user.is_authenticated and self.user not in self.chatroom.users_online.all():
            self.chatroom.users_online.add(self.user)
            self.update_online_count()

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name, self.channel_name
        )

        if self.user.is_authenticated and self.user in self.chatroom.users_online.all():
            self.chatroom.users_online.remove(self.user)
            self.update_online_count()

    def receive(self, text_data):
        data = json.loads(text_data)
        message_body = data.get('body')

        if not self.user.is_authenticated or not message_body:
            return

        message = GroupMessage.objects.create(
            author=self.user,
            group=self.chatroom,
            body=message_body,
        )

        event = {
            'type': 'chat_message',
            'author': self.user.username,
            'body': message.body,
            'timestamp': str(message.created),
        }

        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )

    def chat_message(self, event):
        self.send(text_data=json.dumps({
            'type': 'chat_message',
            'author': event['author'],
            'body': event['body'],
            'timestamp': event['timestamp'],
        }))

    def update_online_count(self):
        count = self.chatroom.users_online.count()
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name,
            {
                'type': 'online_count',
                'count': count,
            }
        )

    def online_count(self, event):
        self.send(text_data=json.dumps({
            'type': 'online_count',
            'online_users': event['count'],
        }))


class OnlineStatusConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.group_name = 'global-status'
        self.group = get_object_or_404(ChatGroup, group_name='public-chat')

        if self.user.is_authenticated:
            self.group.users_online.add(self.user)

        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )
        self.accept()
        self.broadcast_status()

    def disconnect(self, close_code):
        if self.user.is_authenticated:
            self.group.users_online.remove(self.user)

        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
        self.broadcast_status()

    def broadcast_status(self):
        online_users = list(self.group.users_online.exclude(id=self.user.id).values_list('username', flat=True))
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'status_update',
                'users': online_users,
            }
        )

    def status_update(self, event):
        self.send(text_data=json.dumps({
            'type': 'status_update',
            'users_online': event['users'],
        }))
