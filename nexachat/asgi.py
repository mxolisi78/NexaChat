"""
ASGI config for NexaChat.

Routes HTTP requests to Django and WebSocket connections to Channels.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexachat.settings')

# Initialise Django ASGI application BEFORE importing routing
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing  # noqa: E402  (import after Django setup)

application = ProtocolTypeRouter({
    # HTTP -> standard Django
    'http': django_asgi_app,

    # WebSocket -> Channels with session auth
    'websocket': AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})