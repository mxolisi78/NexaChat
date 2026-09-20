"""
WebSocket tests for NexaChat's ChatConsumer.
"""

from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.test import TransactionTestCase

from nexachat.asgi import application
from .models import ChatRoom, Message


class ChatConsumerTests(TransactionTestCase):
    """Integration tests for the WebSocket chat consumer."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='wsuser', password='testpass123'
        )
        self.room = ChatRoom.objects.create(
            name='WS Room',
            slug='ws-room',
            created_by=self.user,
        )

    async def test_connect_and_receive_message(self):
        """A connected client receives its own message back."""
        communicator = WebsocketCommunicator(
            application,
            f'/ws/chat/{self.room.slug}/',
        )
        communicator.scope['user'] = self.user
        communicator.scope['url_route'] = {
            'kwargs': {'slug': self.room.slug}
        }

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Consume the initial "user_join" broadcast
        join_event = await communicator.receive_json_from()
        self.assertEqual(join_event['type'], 'user_join')
        self.assertEqual(join_event['username'], self.user.username)

        # Send a message
        await communicator.send_json_to({'message': 'hello via ws'})

        # We get it back as chat_message
        event = await communicator.receive_json_from()
        self.assertEqual(event['type'], 'chat_message')
        self.assertEqual(event['message'], 'hello via ws')
        self.assertEqual(event['username'], self.user.username)

        await communicator.disconnect()

    async def test_message_persists_to_database(self):
        """Sent messages are saved to the DB."""
        communicator = WebsocketCommunicator(
            application,
            f'/ws/chat/{self.room.slug}/',
        )
        communicator.scope['user'] = self.user
        communicator.scope['url_route'] = {
            'kwargs': {'slug': self.room.slug}
        }

        await communicator.connect()
        await communicator.receive_json_from()  # join event

        await communicator.send_json_to({'message': 'persist me'})
        await communicator.receive_json_from()  # chat_message

        # Check DB
        count = await database_sync_to_async(Message.objects.count)()
        self.assertEqual(count, 1)

        content = await database_sync_to_async(
            lambda: Message.objects.first().content
        )()
        self.assertEqual(content, 'persist me')

        await communicator.disconnect()

    async def test_empty_message_ignored(self):
        """Empty/whitespace messages are not saved or broadcast."""
        communicator = WebsocketCommunicator(
            application,
            f'/ws/chat/{self.room.slug}/',
        )
        communicator.scope['user'] = self.user
        communicator.scope['url_route'] = {
            'kwargs': {'slug': self.room.slug}
        }

        await communicator.connect()
        await communicator.receive_json_from()  # join event

        await communicator.send_json_to({'message': '   '})

        # Nothing should come back
        received = await communicator.receive_nothing(timeout=0.3)
        self.assertTrue(received)

        count = await database_sync_to_async(Message.objects.count)()
        self.assertEqual(count, 0)

        await communicator.disconnect()
