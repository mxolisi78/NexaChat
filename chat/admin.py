"""
Admin registration for NexaChat models.
"""

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils import timezone

from .models import (
    ChatRoom, Message, NewsArticle,
    Friendship, DirectMessage,
    Post, PostLike, PostComment, Story,
    Notification, Profile, Report,
)


# =====================================================================
# Custom admin index — redirect /admin/ to our analytics dashboard
# =====================================================================

def _custom_admin_index(self, request, extra_context=None):
    from .admin_dashboard import admin_dashboard
    return admin_dashboard(request)

AdminSite.index = _custom_admin_index


# =====================================================================
# Chat
# =====================================================================

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_by', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'author', 'short_content', 'timestamp')
    list_filter = ('room', 'timestamp')
    search_fields = ('content', 'author__username')

    def short_content(self, obj):
        return obj.content[:50]
    short_content.short_description = 'Content'


# =====================================================================
# News
# =====================================================================

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'source_name', 'category', 'published_at')
    list_filter = ('category', 'source_name')
    search_fields = ('title', 'description')


# =====================================================================
# Social
# =====================================================================

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'short_content', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')

    def short_content(self, obj):
        return obj.content[:40]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'short_content', 'created_at', 'like_count', 'comment_count')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username')

    def short_content(self, obj):
        return obj.content[:50]


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')
    list_filter = ('created_at',)


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'short_content', 'created_at')
    search_fields = ('content', 'author__username')

    def short_content(self, obj):
        return obj.content[:40]


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('author', 'created_at', 'expires_at')
    list_filter = ('created_at',)
    search_fields = ('author__username', 'content')


# =====================================================================
# Notifications
# =====================================================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'actor__username', 'message')


# =====================================================================
# Profiles
# =====================================================================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'last_seen')
    search_fields = ('user__username', 'location')


# =====================================================================
# Moderation
# =====================================================================

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_target', 'reason', 'status',
        'reporter', 'created_at',
    )
    list_filter = ('status', 'reason', 'target_type', 'created_at')
    search_fields = ('reporter__username', 'target_user__username', 'details')
    readonly_fields = (
        'reporter', 'target_type', 'target_user',
        'target_post', 'target_comment',
        'reason', 'details', 'created_at',
    )
    actions = ['mark_reviewed', 'mark_dismissed']

    def get_target(self, obj):
        if obj.target_user:
            return obj.target_user.username
        if obj.target_post:
            return f"post #{obj.target_post.id}"
        if obj.target_comment:
            return f"comment #{obj.target_comment.id}"
        return '-'
    get_target.short_description = 'Target'

    @admin.action(description='Mark selected reports as reviewed')
    def mark_reviewed(self, request, queryset):
        queryset.update(status='reviewed', reviewed_at=timezone.now())

    @admin.action(description='Dismiss selected reports')
    def mark_dismissed(self, request, queryset):
        queryset.update(status='dismissed', reviewed_at=timezone.now())