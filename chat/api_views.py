"""
REST API views for NexaChat.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer


class ChatRoomListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/rooms/   — list all rooms
    POST /api/rooms/   — create a new room
    """
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Set created_by and ensure unique slug."""
        name = serializer.validated_data.get('name', '')
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while ChatRoom.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        serializer.save(created_by=self.request.user, slug=slug)


class ChatRoomDetailView(generics.RetrieveAPIView):
    """GET /api/rooms/<slug>/ — retrieve a single room."""
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'


class MessageListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/rooms/<slug>/messages/   — list messages
    POST /api/rooms/<slug>/messages/   — post a message
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_room(self):
        return get_object_or_404(ChatRoom, slug=self.kwargs['slug'])

    def get_queryset(self):
        return self.get_room().messages.select_related('author').all()

    def perform_create(self, serializer):
        serializer.save(
            room=self.get_room(),
            author=self.request.user,
        )


class MessageDetailView(generics.RetrieveAPIView):
    """GET /api/rooms/<slug>/messages/<id>/ — retrieve a single message."""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        room = get_object_or_404(ChatRoom, slug=self.kwargs['slug'])
        return room.messages.select_related('author').all()
