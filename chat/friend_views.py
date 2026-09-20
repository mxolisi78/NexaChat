"""
Views for the friend system.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q

from .models import Friendship, Post, Story


@login_required
def friends_home(request):
    """Friends page: list friends, incoming requests, sent requests, suggestions."""
    user = request.user

    friends = Friendship.get_friends(user)

    # Incoming pending requests (someone sent ME a request)
    incoming = Friendship.objects.filter(
        to_user=user, status='pending'
    ).select_related('from_user')

    # Sent pending requests (I sent someone a request)
    outgoing = Friendship.objects.filter(
        from_user=user, status='pending'
    ).select_related('to_user')

    # Suggestions: users I'm not connected to
    connected_ids = set(friends.values_list('id', flat=True))
    connected_ids.add(user.id)
    connected_ids.update(incoming.values_list('from_user_id', flat=True))
    connected_ids.update(outgoing.values_list('to_user_id', flat=True))

    suggestions = User.objects.exclude(id__in=connected_ids).order_by('?')[:8]

    return render(request, 'chat/friends.html', {
        'friends': friends,
        'incoming': incoming,
        'outgoing': outgoing,
        'suggestions': suggestions,
    })


@login_required
def send_friend_request(request, username):
    """Send a friend request to another user."""
    target = get_object_or_404(User, username=username)

    if target == request.user:
        messages.error(request, "You can't add yourself.")
        return redirect('chat:profile', username=username)

    # Already friends?
    if Friendship.are_friends(request.user, target):
        messages.info(request, f"You're already friends with {target.username}.")
        return redirect('chat:profile', username=username)

    # Existing request in either direction?
    existing = Friendship.objects.filter(
        Q(from_user=request.user, to_user=target) |
        Q(from_user=target, to_user=request.user)
    ).first()

    if existing:
        if existing.status == 'pending':
            messages.info(request, "Request already pending.")
        elif existing.status == 'declined':
            # Reset and resend
            existing.status = 'pending'
            existing.from_user = request.user
            existing.to_user = target
            existing.save()
            messages.success(request, f"Friend request sent to {target.username}.")
        return redirect('chat:profile', username=username)

    Friendship.objects.create(from_user=request.user, to_user=target)
    messages.success(request, f"Friend request sent to {target.username}.")
    return redirect('chat:profile', username=username)


@login_required
def accept_friend_request(request, friendship_id):
    """Accept an incoming friend request."""
    friendship = get_object_or_404(
        Friendship, id=friendship_id, to_user=request.user, status='pending'
    )
    friendship.status = 'accepted'
    friendship.save()
    messages.success(request, f"You're now friends with {friendship.from_user.username}!")
    return redirect('chat:friends_home')


@login_required
def decline_friend_request(request, friendship_id):
    """Decline an incoming friend request."""
    friendship = get_object_or_404(
        Friendship, id=friendship_id, to_user=request.user, status='pending'
    )
    friendship.status = 'declined'
    friendship.save()
    messages.info(request, "Friend request declined.")
    return redirect('chat:friends_home')


@login_required
def remove_friend(request, username):
    """Remove a friend (deletes the friendship row)."""
    target = get_object_or_404(User, username=username)

    Friendship.objects.filter(
        Q(from_user=request.user, to_user=target, status='accepted') |
        Q(from_user=target, to_user=request.user, status='accepted')
    ).delete()

    messages.info(request, f"Removed {target.username} from your friends.")
    return redirect('chat:friends_home')


@login_required
def profile(request, username):
    """Public profile page for a user."""
    profile_user = get_object_or_404(User, username=username)
    is_me = profile_user == request.user

    # Friendship state
    friendship = None
    friendship_status = None

    if not is_me:
        friendship = Friendship.objects.filter(
            Q(from_user=request.user, to_user=profile_user) |
            Q(from_user=profile_user, to_user=request.user)
        ).first()
        if friendship:
            friendship_status = friendship.status
            if friendship.status == 'accepted':
                friendship_status = 'friends'

    # Posts — visible if friend or self
    can_view_posts = is_me or Friendship.are_friends(request.user, profile_user)
    posts = profile_user.posts.all()[:20] if can_view_posts else []

    # Counts
    friend_count = Friendship.get_friends(profile_user).count()
    post_count = profile_user.posts.count()

    return render(request, 'chat/profile.html', {
        'profile_user': profile_user,
        'is_me': is_me,
        'friendship': friendship,
        'friendship_status': friendship_status,
        'posts': posts,
        'can_view_posts': can_view_posts,
        'friend_count': friend_count,
        'post_count': post_count,
    })
