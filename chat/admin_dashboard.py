"""
Custom admin dashboard — KPIs, chart, moderation queue.
"""

from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from .models import (
    ChatRoom, Message, Post, DirectMessage,
    Notification, Report, Story, Profile,
)


@staff_member_required
def admin_dashboard(request):
    """Custom admin index with KPIs and charts."""

    # ─── KPI counts ───
    total_users = User.objects.count()
    total_rooms = ChatRoom.objects.count()
    total_messages = Message.objects.count()
    total_posts = Post.objects.count()
    total_dms = DirectMessage.objects.count()
    total_stories = Story.objects.count()
    pending_reports = Report.objects.filter(status='pending').count()

    # Users active in last 24h (based on profile.last_seen)
    one_day_ago = timezone.now() - timedelta(hours=24)
    active_users = Profile.objects.filter(last_seen__gte=one_day_ago).count()

    # ─── Registrations over last 14 days ───
    fourteen_days_ago = timezone.now() - timedelta(days=14)
    daily_registrations = (
        User.objects
        .filter(date_joined__gte=fourteen_days_ago)
        .annotate(day=TruncDate('date_joined'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    # Build a continuous 14-day series (fill gaps with 0)
    reg_by_day = {item['day']: item['count'] for item in daily_registrations}
    reg_series = []
    max_reg = 1
    for i in range(13, -1, -1):
        day = (timezone.now() - timedelta(days=i)).date()
        count = reg_by_day.get(day, 0)
        reg_series.append({'day': day, 'count': count})
        max_reg = max(max_reg, count)

    for point in reg_series:
        point['pct'] = int((point['count'] / max_reg) * 100) if max_reg else 0

    # ─── Messages over last 14 days ───
    daily_messages = (
        Message.objects
        .filter(timestamp__gte=fourteen_days_ago)
        .annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    msg_by_day = {item['day']: item['count'] for item in daily_messages}
    msg_series = []
    max_msg = 1
    for i in range(13, -1, -1):
        day = (timezone.now() - timedelta(days=i)).date()
        count = msg_by_day.get(day, 0)
        msg_series.append({'day': day, 'count': count})
        max_msg = max(max_msg, count)

    for point in msg_series:
        point['pct'] = int((point['count'] / max_msg) * 100) if max_msg else 0

    # ─── Pending reports (latest 5) ───
    recent_reports = (
        Report.objects
        .filter(status='pending')
        .select_related('reporter', 'target_user')
        .order_by('-created_at')[:5]
    )

    # ─── Recent users (latest 5) ───
    recent_users = User.objects.order_by('-date_joined')[:5]

    # ─── Recent posts (latest 5) ───
    recent_posts = Post.objects.select_related('author').order_by('-created_at')[:5]

    context = {
        # KPIs
        'total_users': total_users,
        'active_users': active_users,
        'total_rooms': total_rooms,
        'total_messages': total_messages,
        'total_posts': total_posts,
        'total_dms': total_dms,
        'total_stories': total_stories,
        'pending_reports': pending_reports,

        # Charts
        'reg_series': reg_series,
        'msg_series': msg_series,

        # Lists
        'recent_reports': recent_reports,
        'recent_users': recent_users,
        'recent_posts': recent_posts,
    }

    return render(request, 'admin/dashboard.html', context)