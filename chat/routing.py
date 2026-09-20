"""
WebSocket URL routing for NexaChat.
"""

from django.urls import path
from . import consumers
from . import notification_consumer

websocket_urlpatterns = [
    path('ws/chat/<slug:slug>/', consumers.ChatConsumer.as_asgi()),
    path('ws/dm/<str:username>/', consumers.DirectMessageConsumer.as_asgi()),
    path('ws/notifications/', notification_consumer.NotificationConsumer.as_asgi()),
]
