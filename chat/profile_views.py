"""
Profile and account settings views.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

from .forms import ProfileForm, AccountForm
from .models import Profile


@login_required
def profile_settings(request):
    """Edit avatar, bio, location."""
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
            return redirect('chat:profile_settings')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'chat/profile_settings.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def account_settings(request):
    """Edit email, name."""
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Account updated!")
            return redirect('chat:account_settings')
    else:
        form = AccountForm(instance=request.user)

    return render(request, 'chat/account_settings.html', {'form': form})


@login_required
def change_password(request):
    """Change password."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep session alive
            messages.success(request, "Password changed!")
            return redirect('chat:account_settings')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'chat/change_password.html', {'form': form})
