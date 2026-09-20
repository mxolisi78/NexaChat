"""
Reporting / moderation views.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages as flash
from django.utils import timezone

from .models import Report, Post, PostComment


@login_required
def report_post(request, post_id):
    """Report a post."""
    post = get_object_or_404(Post, id=post_id)

    if post.author == request.user:
        flash.error(request, "You can't report your own post.")
        return redirect('chat:feed')

    existing = Report.objects.filter(
        reporter=request.user,
        target_post=post,
        status='pending',
    ).exists()
    if existing:
        flash.info(request, "You already reported this post.")
        return redirect('chat:feed')

    if request.method == 'POST':
        reason = request.POST.get('reason', 'other')
        details = request.POST.get('details', '').strip()[:500]

        Report.objects.create(
            reporter=request.user,
            target_type='post',
            target_post=post,
            target_user=post.author,
            reason=reason,
            details=details,
        )
        flash.success(request, "Report submitted. Our moderators will review it.")
        return redirect('chat:feed')

    return render(request, 'chat/report_form.html', {
        'target_type': 'post',
        'target_label': f"Post by {post.author.username}",
        'target_preview': post.content[:200],
        'reasons': Report.REASON_CHOICES,
        'cancel_url': 'chat:feed',
    })


@login_required
def report_user(request, username):
    """Report a user."""
    target = get_object_or_404(User, username=username)

    if target == request.user:
        flash.error(request, "You can't report yourself.")
        return redirect('chat:profile', username=username)

    existing = Report.objects.filter(
        reporter=request.user,
        target_user=target,
        target_type='user',
        status='pending',
    ).exists()
    if existing:
        flash.info(request, "You already reported this user.")
        return redirect('chat:profile', username=username)

    if request.method == 'POST':
        reason = request.POST.get('reason', 'other')
        details = request.POST.get('details', '').strip()[:500]

        Report.objects.create(
            reporter=request.user,
            target_type='user',
            target_user=target,
            reason=reason,
            details=details,
        )
        flash.success(request, "Report submitted.")
        return redirect('chat:profile', username=username)

    return render(request, 'chat/report_form.html', {
        'target_type': 'user',
        'target_label': f"User {target.username}",
        'target_preview': (target.profile.bio if hasattr(target, 'profile') else '') or '(no bio)',
        'reasons': Report.REASON_CHOICES,
        'cancel_url': 'chat:profile',
        'cancel_arg': target.username,
    })


@login_required
def report_comment(request, comment_id):
    """Report a comment."""
    comment = get_object_or_404(PostComment, id=comment_id)

    if comment.author == request.user:
        flash.error(request, "You can't report your own comment.")
        return redirect('chat:feed')

    existing = Report.objects.filter(
        reporter=request.user,
        target_comment=comment,
        status='pending',
    ).exists()
    if existing:
        flash.info(request, "You already reported this comment.")
        return redirect('chat:feed')

    if request.method == 'POST':
        reason = request.POST.get('reason', 'other')
        details = request.POST.get('details', '').strip()[:500]

        Report.objects.create(
            reporter=request.user,
            target_type='comment',
            target_comment=comment,
            target_user=comment.author,
            reason=reason,
            details=details,
        )
        flash.success(request, "Report submitted.")
        return redirect('chat:feed')

    return render(request, 'chat/report_form.html', {
        'target_type': 'comment',
        'target_label': f"Comment by {comment.author.username}",
        'target_preview': comment.content[:200],
        'reasons': Report.REASON_CHOICES,
        'cancel_url': 'chat:feed',
    })


@login_required
def my_reports(request):
    """Show the current user's submitted reports."""
    reports = Report.objects.filter(
        reporter=request.user
    ).select_related('target_user').order_by('-created_at')

    return render(request, 'chat/my_reports.html', {'reports': reports})