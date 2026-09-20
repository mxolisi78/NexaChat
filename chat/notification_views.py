"""
Views for the notification system.
"""

from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def list_notifications(request):
    """Return last 15 notifications as JSON for the dropdown."""
    notes = Notification.objects.filter(
        recipient=request.user
    ).select_related('actor')[:15]

    data = [{
        'id': n.id,
        'type': n.notification_type,
        'actor': n.actor.username,
        'message': n.message,
        'url': n.url,
        'is_read': n.is_read,
        'created': n.created_at.isoformat(),
    } for n in notes]

    return JsonResponse({
        'notifications': data,
        'unread_count': Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count(),
    })


@login_required
def unread_count(request):
    """Return just the unread count — used for the navbar badge."""
    count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()
    return JsonResponse({'count': count})


@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications as read."""
    Notification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True)
    return JsonResponse({'ok': True})


@login_required
def open_notification(request, notification_id):
    """Mark one notification as read and redirect to its URL."""
    note = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    note.is_read = True
    note.save(update_fields=['is_read'])

    if note.url:
        return redirect(note.url)
    return redirect('chat:dashboard')
