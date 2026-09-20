"""
Views for stories — 24-hour ephemeral posts.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as flash
from django.utils import timezone
from datetime import timedelta

from .models import Story, Friendship
from .forms import StoryForm


@login_required
def create_story(request):
    """Create a new story that expires in 24 hours."""
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.author = request.user
            story.expires_at = timezone.now() + timedelta(hours=24)
            story.save()
            flash.success(request, "Story posted! It will disappear in 24 hours.")
            return redirect('chat:feed')
    else:
        form = StoryForm()
    return render(request, 'chat/story_create.html', {'form': form})


@login_required
def view_story(request, story_id):
    """View a single story (redirects to feed — modal handles display)."""
    story = get_object_or_404(Story, id=story_id)
    if not story.is_active:
        flash.info(request, "That story has expired.")
        return redirect('chat:feed')
    return redirect('chat:feed')


@login_required
def delete_story(request, story_id):
    """Delete a story you own."""
    story = get_object_or_404(Story, id=story_id, author=request.user)
    story.delete()
    flash.info(request, "Story deleted.")
    return redirect('chat:feed')


def group_stories_for_feed(user):
    """Return grouped stories for the feed's story bar."""
    friend_ids = list(Friendship.get_friends(user).values_list('id', flat=True))
    friend_ids.append(user.id)

    active = (
        Story.objects
        .filter(author_id__in=friend_ids, expires_at__gt=timezone.now())
        .select_related('author')
        .order_by('-created_at')
    )

    grouped = {}
    for story in active:
        grouped.setdefault(story.author, []).append(story)

    result = []
    if user in grouped:
        result.append({'author': user, 'stories': grouped.pop(user), 'is_self': True})
    for author, stories in grouped.items():
        result.append({'author': author, 'stories': stories, 'is_self': False})

    return result