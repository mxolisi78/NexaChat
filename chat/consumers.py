"""
WebSocket consumers for NexaChat.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth.models import User


# =====================================================================
# Public room chat
# =====================================================================

class ChatConsumer(AsyncWebsocketConsumer):
    """Handles WebSocket connections for a single public chat room."""

    async def connect(self):
        self.room_slug = self.scope['url_route']['kwargs']['slug']
        self.room_group_name = f'chat_{self.room_slug}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'user_join',
            'username': self.user.username,
        })

    async def disconnect(self, close_code):
        if not hasattr(self, 'room_group_name'):
            return
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'user_leave',
            'username': getattr(self.user, 'username', 'Someone'),
        })
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        content = (data.get('message') or '').strip()
        if not content:
            return
        msg = await self.save_message(content)
        if msg is None:
            return
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat_message',
            'message': content,
            'username': self.user.username,
            'timestamp': msg['timestamp'],
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))

    async def user_join(self, event):
        await self.send(text_data=json.dumps({'type': 'user_join', 'username': event['username']}))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({'type': 'user_leave', 'username': event['username']}))

    @database_sync_to_async
    def save_message(self, content):
        from .models import ChatRoom, Message
        try:
            room = ChatRoom.objects.get(slug=self.room_slug)
        except ChatRoom.DoesNotExist:
            return None
        message = Message.objects.create(room=room, author=self.user, content=content)
        return {
            'id': message.id,
            'timestamp': timezone.localtime(message.timestamp).strftime('%b %d, %H:%M'),
        }


# =====================================================================
# Direct messages (1-on-1, friends only)
# =====================================================================

class DirectMessageConsumer(AsyncWebsocketConsumer):
    """
    WebSocket for 1-on-1 DMs.

    Each user has a personal group named `user_<id>`.
    When A messages B:
      1. Save to DB
      2. Broadcast to A's group (so A sees their own message)
      3. Broadcast to B's group (so B sees it instantly)
    """

    async def connect(self):
        self.other_username = self.scope['url_route']['kwargs']['username']
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Verify friendship
        other = await self.get_user(self.other_username)
        if other is None:
            await self.close()
            return

        is_friend = await self.are_friends(self.user, other)
        if not is_friend:
            await self.close()
            return

        self.other_user = other
        self.other_group = f'user_{other.id}'
        self.my_group = f'user_{self.user.id}'

        # Join both groups — we receive our own messages too
        await self.channel_layer.group_add(self.my_group, self.channel_name)
        await self.channel_layer.group_add(self.other_group, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'my_group'):
            await self.channel_layer.group_discard(self.my_group, self.channel_name)
        if hasattr(self, 'other_group'):
            await self.channel_layer.group_discard(self.other_group, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        content = (data.get('message') or '').strip()
        if not content:
            return

        saved = await self.save_dm(content)
        if saved is None:
            return

        payload = {
            'type': 'dm_message',
            'message': content,
            'sender': self.user.username,
            'recipient': self.other_user.username,
            'timestamp': saved['timestamp'],
        }

        # Broadcast to both users' personal groups
        await self.channel_layer.group_send(self.my_group, payload)
        if self.other_group != self.my_group:
            await self.channel_layer.group_send(self.other_group, payload)

    async def dm_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'dm_message',
            'message': event['message'],
            'sender': event['sender'],
            'recipient': event['recipient'],
            'timestamp': event['timestamp'],
        }))

    # ---------------- DB helpers ----------------

    @database_sync_to_async
    def get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def are_friends(self, a, b):
        from .models import Friendship
        return Friendship.are_friends(a, b)

    @database_sync_to_async
    def save_dm(self, content):
        from .models import DirectMessage
        dm = DirectMessage.objects.create(
            sender=self.user,
            recipient=self.other_user,
            content=content,
        )
        return {
            'id': dm.id,
            'timestamp': timezone.localtime(dm.timestamp).strftime('%b %d, %H:%M'),
        }
