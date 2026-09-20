"""
DRF serializers for NexaChat.
"""

from rest_framework import serializers
from .models import ChatRoom, Message


class MessageSerializer(serializers.ModelSerializer):
    """Serialize a Message with author username."""

    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'author', 'content', 'timestamp')
        read_only_fields = ('id', 'author', 'timestamp')


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serialize a ChatRoom with creator and message count."""

    created_by = serializers.CharField(source='created_by.username', read_only=True)
    message_count = serializers.IntegerField(source='messages.count', read_only=True)

    class Meta:
        model = ChatRoom
        fields = (
            'id', 'name', 'slug', 'description',
            'created_by', 'created_at', 'message_count',
        )
        read_only_fields = ('id', 'slug', 'created_by', 'created_at', 'message_count')
