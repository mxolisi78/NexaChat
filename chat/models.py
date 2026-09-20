"""
Database models for NexaChat.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# =====================================================================
# Chat rooms & messages
# =====================================================================

class ChatRoom(models.Model):
    """A public chat room where users exchange messages."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_rooms',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Message(models.Model):
    """A single message posted in a chat room."""

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.author.username}: {self.content[:40]}"


# =====================================================================
# News
# =====================================================================

class NewsArticle(models.Model):
    """Cached news article from external API."""

    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('technology', 'Technology'),
        ('business', 'Business'),
        ('sports', 'Sports'),
        ('science', 'Science'),
    ]

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    url = models.URLField(max_length=1000, unique=True)
    image_url = models.URLField(max_length=1000, blank=True)
    source_name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    published_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title[:60]


# =====================================================================
# Social: Friendships
# =====================================================================

class Friendship(models.Model):
    """
    A friend relationship between two users.

    One row per relationship:
      from_user = sender, to_user = receiver
      status = 'pending' | 'accepted' | 'declined'
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_friend_requests',
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_friend_requests',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user.username} → {self.to_user.username} ({self.status})"

    @staticmethod
    def are_friends(user_a, user_b):
        return Friendship.objects.filter(
            models.Q(from_user=user_a, to_user=user_b, status='accepted') |
            models.Q(from_user=user_b, to_user=user_a, status='accepted')
        ).exists()

    @staticmethod
    def get_friends(user):
        sent = Friendship.objects.filter(
            from_user=user, status='accepted'
        ).values_list('to_user', flat=True)
        received = Friendship.objects.filter(
            to_user=user, status='accepted'
        ).values_list('from_user', flat=True)
        return User.objects.filter(models.Q(id__in=sent) | models.Q(id__in=received))


# =====================================================================
# Social: Direct messages
# =====================================================================

class DirectMessage(models.Model):
    """A private 1-on-1 message between two users."""

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_dms',
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_dms',
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}: {self.content[:40]}"

    @staticmethod
    def conversation_between(user_a, user_b):
        return DirectMessage.objects.filter(
            models.Q(sender=user_a, recipient=user_b) |
            models.Q(sender=user_b, recipient=user_a)
        ).select_related('sender', 'recipient').order_by('timestamp')


# =====================================================================
# Social: Posts
# =====================================================================

class Post(models.Model):
    """A status update / post from a user."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
    )
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.username}: {self.content[:50]}"

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()


class PostLike(models.Model):
    """A like on a post."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')


class PostComment(models.Model):
    """A comment on a post."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username} on post {self.post_id}"


# =====================================================================
# Social: Stories (24-hour ephemeral posts)
# =====================================================================

class Story(models.Model):
    """A story — visible for 24 hours, then hidden."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stories',
    )
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='stories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.username} story @ {self.created_at}"

    @property
    def is_active(self):
        from django.utils import timezone
        return self.expires_at > timezone.now()

    @staticmethod
    def active_stories_for(user):
        from django.utils import timezone
        friends = Friendship.get_friends(user)
        author_ids = list(friends.values_list('id', flat=True)) + [user.id]
        return Story.objects.filter(
            author_id__in=author_ids,
            expires_at__gt=timezone.now(),
        ).select_related('author').order_by('-created_at')


# =====================================================================
# Notifications
# =====================================================================

class Notification(models.Model):
    """A notification for a user about an event."""

    TYPE_CHOICES = [
        ('friend_request', 'Friend Request'),
        ('friend_accept', 'Friend Accepted'),
        ('post_like', 'Post Like'),
        ('post_comment', 'Post Comment'),
        ('dm', 'Direct Message'),
        ('story', 'New Story'),
        ('mention', 'Mention'),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='triggered_notifications',
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor.username} → {self.recipient.username}: {self.message}"

    @staticmethod
    def create(recipient, actor, notification_type, message, url=''):
        """
        Create a notification and broadcast it over WebSocket.

        Never raises — if the broadcast fails, we still return the
        saved notification. This prevents notifications from breaking
        the main request flow.
        """
        if recipient == actor:
            return None

        note = Notification.objects.create(
            recipient=recipient,
            actor=actor,
            notification_type=notification_type,
            message=message,
            url=url,
        )

        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            unread = Notification.objects.filter(
                recipient=recipient, is_read=False
            ).count()

            async_to_sync(channel_layer.group_send)(
                f'notify_{recipient.id}',
                {
                    'type': 'notify',
                    'id': note.id,
                    'notification_type': notification_type,
                    'actor': actor.username,
                    'message': message,
                    'url': url,
                    'unread_count': unread,
                },
            )
        except Exception:
            pass

        return note


# =====================================================================
# User Profiles
# =====================================================================

class Profile(models.Model):
    """Extended user info — avatar, bio, location, last seen."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
    )
    bio = models.CharField(max_length=300, blank=True)
    location = models.CharField(max_length=100, blank=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def is_online(self):
        """True if the user was active within the last 5 minutes."""
        from django.utils import timezone
        from datetime import timedelta
        if not self.last_seen:
            return False
        return self.last_seen > timezone.now() - timedelta(minutes=5)

    @property
    def avatar_url(self):
        """Safe avatar URL — falls back to None if no avatar."""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return None


# =====================================================================
# Moderation: Reports
# =====================================================================

class Report(models.Model):
    """A user-submitted report about content or another user."""

    REASON_CHOICES = [
        ('spam', 'Spam or advertising'),
        ('harassment', 'Harassment or bullying'),
        ('hate', 'Hate speech'),
        ('inappropriate', 'Inappropriate content'),
        ('fake', 'Fake account'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending review'),
        ('reviewed', 'Reviewed - action taken'),
        ('dismissed', 'Dismissed'),
    ]

    TARGET_CHOICES = [
        ('user', 'User'),
        ('post', 'Post'),
        ('comment', 'Comment'),
    ]

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_made',
    )
    target_type = models.CharField(max_length=10, choices=TARGET_CHOICES)
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_against',
        null=True, blank=True,
    )
    target_post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='reports',
        null=True, blank=True,
    )
    target_comment = models.ForeignKey(
        'PostComment',
        on_delete=models.CASCADE,
        related_name='reports',
        null=True, blank=True,
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.TextField(max_length=500, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        target = self.target_type
        if self.target_user:
            target += f":{self.target_user.username}"
        elif self.target_post:
            target += f":post#{self.target_post.id}"
        elif self.target_comment:
            target += f":comment#{self.target_comment.id}"
        return f"Report({target}) by {self.reporter.username} � {self.status}"
