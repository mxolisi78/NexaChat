"""
Views for direct messages (1-on-1 chats between friends).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages as flash
from django.db.models import Q, Max

from .models import DirectMessage, Friendship


@login_required
def inbox(request):
    """List all conversations the user has with friends."""
    user = request.user
    friends = Friendship.get_friends(user)

    conversations = []
    for friend in friends:
        last_msg = DirectMessage.conversation_between(user, friend).last()
        unread = DirectMessage.objects.filter(
            sender=friend, recipient=user, is_read=False
        ).count()
        conversations.append({
            'user': friend,
            'last_message': last_msg,
            'unread': unread,
        })

    # Sort by most recent
    conversations.sort(
        key=lambda c: c['last_message'].timestamp if c['last_message'] else None,
        reverse=True,
    )

    total_unread = DirectMessage.objects.filter(
        recipient=user, is_read=False
    ).count()

    return render(request, 'chat/dm_inbox.html', {
        'conversations': conversations,
        'total_unread': total_unread,
    })


@login_required
def conversation(request, username):
    """Show a 1-on-1 chat with another user (friends only)."""
    other = get_object_or_404(User, username=username)

    if other == request.user:
        flash.error(request, "You can't message yourself.")
        return redirect('chat:dm_inbox')

    if not Friendship.are_friends(request.user, other):
        flash.error(request, f"You must be friends with {other.username} to message them.")
        return redirect('chat:profile', username=other.username)

    # Mark all incoming messages as read
    DirectMessage.objects.filter(
        sender=other, recipient=request.user, is_read=False
    ).update(is_read=True)

    messages_qs = DirectMessage.conversation_between(request.user, other)

    return render(request, 'chat/dm_conversation.html', {
        'other_user': other,
        'messages': messages_qs,
    })
