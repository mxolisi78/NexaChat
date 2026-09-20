"""
REST API URL routing for NexaChat.
"""

from django.urls import path
from . import api_views, auth_views

app_name = 'chat_api'

urlpatterns = [
    # Auth
    path('auth/register/', auth_views.register, name='register'),
    path('auth/login/', auth_views.login, name='login'),
    path('auth/logout/', auth_views.logout, name='logout'),
    path('auth/me/', auth_views.me, name='me'),

    # Rooms
    path('rooms/', api_views.ChatRoomListCreateView.as_view(), name='room_list'),
    path('rooms/<slug:slug>/', api_views.ChatRoomDetailView.as_view(), name='room_detail'),

    # Messages
    path('rooms/<slug:slug>/messages/',
         api_views.MessageListCreateView.as_view(),
         name='message_list'),
    path('rooms/<slug:slug>/messages/<int:id>/',
         api_views.MessageDetailView.as_view(),
         name='message_detail'),
]
