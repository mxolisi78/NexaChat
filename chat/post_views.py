"""
Views for posts, feed, likes, and comments.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q

from .models import Post, PostLike, PostComment, Friendship
from .forms import PostForm, CommentForm
from .story_views import group_stories_for_feed


def _visible_authors(user):
    friend_ids = list(Friendship.get_friends(user).values_list('id', flat=True))
    return User.objects.filter(Q(id=user.id) | Q(id__in=friend_ids))


@login_required
def feed(request):
    authors = _visible_authors(request.user)
    posts = (
        Post.objects
        .filter(author__in=authors)
        .select_related('author')
        .prefetch_related('likes', 'comments__author')
    )

    form = PostForm()
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Post published!")
            return redirect('chat:feed')

    liked_ids = set(
        PostLike.objects.filter(user=request.user).values_list('post_id', flat=True)
    )

    story_groups = group_stories_for_feed(request.user)

    return render(request, 'chat/feed.html', {
        'posts': posts,
        'form': form,
        'liked_ids': liked_ids,
        'comment_form': CommentForm(),
        'story_groups': story_groups,
    })


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Post published!")
            return redirect('chat:feed')
    else:
        form = PostForm()
    return render(request, 'chat/post_create.html', {'form': form})


@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user and not Friendship.are_friends(request.user, post.author):
        messages.error(request, "You can't interact with this post.")
        return redirect('chat:feed')
    like, created = PostLike.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
    return redirect(request.META.get('HTTP_REFERER', 'chat:feed'))


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user and not Friendship.are_friends(request.user, post.author):
        messages.error(request, "You can't comment on this post.")
        return redirect('chat:feed')
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Comment can't be empty.")
    return redirect(request.META.get('HTTP_REFERER', 'chat:feed'))


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    post.delete()
    messages.info(request, "Post deleted.")
    return redirect('chat:feed')
