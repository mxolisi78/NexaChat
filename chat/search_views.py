"""
Global search — users, rooms, posts.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from .models import ChatRoom, Post, Friendship


@login_required
def search(request):
    """Search users, rooms, and posts."""
    query = (request.GET.get('q') or '').strip()
    search_type = request.GET.get('type', 'all')

    users = User.objects.none()
    rooms = ChatRoom.objects.none()
    posts = Post.objects.none()

    if query:
        # Users
        if search_type in ('all', 'users'):
            users = (
                User.objects
                .filter(
                    Q(username__icontains=query) |
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query)
                )
                .exclude(id=request.user.id)
                .order_by('username')[:20]
            )

        # Rooms
        if search_type in ('all', 'rooms'):
            rooms = (
                ChatRoom.objects
                .filter(
                    Q(name__icontains=query) |
                    Q(description__icontains=query)
                )
                .order_by('-created_at')[:20]
            )

        # Posts — only from friends + self
        if search_type in ('all', 'posts'):
            friend_ids = list(
                Friendship.get_friends(request.user).values_list('id', flat=True)
            )
            visible_ids = friend_ids + [request.user.id]
            posts = (
                Post.objects
                .filter(author_id__in=visible_ids)
                .filter(content__icontains=query)
                .select_related('author')
                .order_by('-created_at')[:20]
            )

    context = {
        'query': query,
        'search_type': search_type,
        'users': users,
        'rooms': rooms,
        'posts': posts,
        'user_count': users.count() if query else 0,
        'room_count': rooms.count() if query else 0,
        'post_count': posts.count() if query else 0,
    }
    return render(request, 'chat/search.html', context)