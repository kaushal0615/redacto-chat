from django.db import models
from django.contrib.auth.models import User
import shortuuid
import os
from PIL import Image

class ChatGroup(models.Model):
    group_name = models.CharField(max_length=128, unique=True, blank=True)
    groupchat_name = models.CharField(max_length=128, null=True, blank=True)
    admin = models.ForeignKey(User, related_name='groupchats', null=True, blank=True, on_delete=models.SET_NULL)
    users_online = models.ManyToManyField(User, related_name='online_in_groups', blank=True)
    members = models.ManyToManyField(User, related_name='chat_groups', blank=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.group_name

    def save(self, *args, **kwargs):
        if not self.group_name:
            self.group_name = shortuuid.uuid()
        super().save(*args, **kwargs)


class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup, related_name='chat_messages', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length=300, blank=True, null=True)
    file = models.FileField(upload_to='files/', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.body:
            return f"{self.author.username}: {self.body}"
        elif self.file:
            return f"{self.author.username}: {self.filename}"

    @property
    def filename(self):
        return os.path.basename(self.file.name) if self.file else None

    @property
    def is_image(self):
        try:
            img = Image.open(self.file)
            img.verify()
            return True
        except:
            return False

    class Meta:
        ordering = ['-created']


