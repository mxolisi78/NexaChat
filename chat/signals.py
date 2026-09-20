"""
Signal handlers — automatically create notifications on key events.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import (
    Friendship, PostLike, PostComment, DirectMessage, Story, Notification
)


@receiver(post_save, sender=Friendship)
def on_friend_request(sender, instance, created, **kwargs):
    """Notify the recipient when a friend request is sent or accepted."""
    if created and instance.status == 'pending':
        Notification.create(
            recipient=instance.to_user,
            actor=instance.from_user,
            notification_type='friend_request',
            message=f"{instance.from_user.username} sent you a friend request",
            url=reverse('chat:friends_home'),
        )
    elif not created and instance.status == 'accepted':
        Notification.create(
            recipient=instance.from_user,
            actor=instance.to_user,
            notification_type='friend_accept',
            message=f"{instance.to_user.username} accepted your friend request",
            url=reverse('chat:profile', args=[instance.to_user.username]),
        )


@receiver(post_save, sender=PostLike)
def on_post_like(sender, instance, created, **kwargs):
    """Notify the post author when someone likes their post."""
    if created:
        post = instance.post
        Notification.create(
            recipient=post.author,
            actor=instance.user,
            notification_type='post_like',
            message=f"{instance.user.username} liked your post",
            url=reverse('chat:feed') + f'#post-{post.id}',
        )


@receiver(post_save, sender=PostComment)
def on_post_comment(sender, instance, created, **kwargs):
    """Notify the post author when someone comments."""
    if created:
        post = instance.post
        Notification.create(
            recipient=post.author,
            actor=instance.author,
            notification_type='post_comment',
            message=f"{instance.author.username} commented on your post",
            url=reverse('chat:feed') + f'#post-{post.id}',
        )


@receiver(post_save, sender=DirectMessage)
def on_direct_message(sender, instance, created, **kwargs):
    """Notify the recipient of a new DM."""
    if created:
        Notification.create(
            recipient=instance.recipient,
            actor=instance.sender,
            notification_type='dm',
            message=f"New message from {instance.sender.username}",
            url=reverse('chat:dm', args=[instance.sender.username]),
        )


@receiver(post_save, sender=Story)
def on_new_story(sender, instance, created, **kwargs):
    """Notify all friends when someone posts a story."""
    if not created:
        return
    # Skip if story is expired
    if not instance.is_active:
        return

    for friend in Friendship.get_friends(instance.author):
        Notification.create(
            recipient=friend,
            actor=instance.author,
            notification_type='story',
            message=f"{instance.author.username} posted a new story",
            url=reverse('chat:feed'),
        )


# =====================================================================
# Auto-create Profile on User creation
# =====================================================================

from django.contrib.auth.models import User
from .models import Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile whenever a new User is created."""
    if created:
        Profile.objects.get_or_create(user=instance)
