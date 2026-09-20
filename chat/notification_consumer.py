"""
WebSocket consumer for real-time notifications.

Each user has a personal group `notify_<user_id>`.
Whenever a Notification is created, we broadcast to that group.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncWebsocketConsumer):
    """Sends real-time notifications to a single logged-in user."""

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f'notify_{self.user.id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send current unread count on connect
        count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'init',
            'unread_count': count,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notify(self, event):
        """Broadcast a notification to the client."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'id': event['id'],
            'notification_type': event['notification_type'],
            'actor': event['actor'],
            'message': event['message'],
            'url': event['url'],
            'unread_count': event['unread_count'],
        }))

    @database_sync_to_async
    def get_unread_count(self):
        from .models import Notification
        return Notification.objects.filter(
            recipient=self.user, is_read=False
        ).count()
