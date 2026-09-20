"""
Views for the NexaChat chat app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Count

from .forms import SignUpForm, MessageForm, ChatRoomForm
from .models import ChatRoom, Message
from . import news_service


def home(request):
    """Landing page for NexaChat."""
    return render(request, 'chat/home.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('chat:dashboard')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to NexaChat, {user.username}!")
            return redirect('chat:dashboard')
    else:
        form = SignUpForm()
    return render(request, 'chat/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('chat:dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('chat:dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'chat/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You've been logged out.")
    return redirect('chat:home')


@login_required
def dashboard(request):
    user = request.user
    stats = {
        'total_rooms': ChatRoom.objects.count(),
        'total_messages': Message.objects.count(),
        'my_messages': Message.objects.filter(author=user).count(),
        'my_rooms': ChatRoom.objects.filter(created_by=user).count(),
    }
    owned_rooms = (ChatRoom.objects.filter(created_by=user)
                   .annotate(msg_count=Count('messages'))
                   .order_by('-created_at')[:6])
    recent_rooms = (ChatRoom.objects.annotate(msg_count=Count('messages'))
                    .order_by('-created_at')[:6])
    recent_messages = (Message.objects.select_related('author', 'room')
                       .order_by('-timestamp')[:8])

    # News widget
    news_articles = news_service.get_recent_articles(limit=5)

    return render(request, 'chat/dashboard.html', {
        'stats': stats,
        'owned_rooms': owned_rooms,
        'recent_rooms': recent_rooms,
        'recent_messages': recent_messages,
        'news_articles': news_articles,
    })


@login_required
def news_feed(request):
    """Dedicated news feed page."""
    category = request.GET.get('category', 'general')

    # Refresh cache if stale
    if news_service.cache_is_stale(category, hours=6):
        news_service.fetch_and_cache(category=category, limit=10)

    articles = news_service.get_recent_articles(category=category, limit=30)

    return render(request, 'chat/news.html', {
        'articles': articles,
        'current_category': category,
    })


@login_required
def room_list(request):
    rooms = ChatRoom.objects.annotate(msg_count=Count('messages'))
    return render(request, 'chat/room_list.html', {'rooms': rooms})


@login_required
def room_create(request):
    if request.method == 'POST':
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.created_by = request.user
            base_slug = slugify(room.name)
            slug = base_slug
            counter = 1
            while ChatRoom.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            room.slug = slug
            room.save()
            messages.success(request, f"Room #{room.name} created!")
            return redirect('chat:room_detail', slug=room.slug)
    else:
        form = ChatRoomForm()
    return render(request, 'chat/room_create.html', {'form': form})


@login_required
def room_detail(request, slug):
    room = get_object_or_404(ChatRoom, slug=slug)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.room = room
            message.author = request.user
            message.save()
            return redirect('chat:room_detail', slug=room.slug)
    else:
        form = MessageForm()
    room_messages = room.messages.select_related('author').all()
    return render(request, 'chat/room_detail.html', {
        'room': room,
        'room_messages': room_messages,
        'form': form,
    })
