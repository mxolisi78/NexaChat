"""
Forms for the chat app.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    Message, ChatRoom, Post, PostComment, Story, Profile,
)


# =====================================================================
# Authentication
# =====================================================================

class SignUpForm(UserCreationForm):
    """Custom signup form with email required."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'you@example.com',
        }),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-input')
            field.widget.attrs.setdefault('placeholder', field.label)


# =====================================================================
# Chat
# =====================================================================

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('content',)
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Type a message... (Enter to send)',
                'autocomplete': 'off',
                'id': 'message-input',
            }),
        }
        labels = {'content': ''}


class ChatRoomForm(forms.ModelForm):
    class Meta:
        model = ChatRoom
        fields = ('name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Room name (e.g. General)',
                'maxlength': 100,
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Short description (optional)',
                'maxlength': 255,
            }),
        }
        labels = {'name': '', 'description': ''}


# =====================================================================
# Posts & comments
# =====================================================================

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('content', 'image')
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': "What's on your mind?",
                'rows': 3,
                'style': 'resize: vertical; font-family: inherit;',
            }),
        }
        labels = {'content': '', 'image': ''}


class CommentForm(forms.ModelForm):
    class Meta:
        model = PostComment
        fields = ('content',)
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Write a comment...',
                'autocomplete': 'off',
                'style': 'margin-bottom: 0;',
            }),
        }
        labels = {'content': ''}


# =====================================================================
# Stories
# =====================================================================

class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ('content', 'image')
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Add a caption (optional)',
                'maxlength': 200,
            }),
            'image': forms.ClearableFileInput(attrs={
                'accept': 'image/*',
                'style': 'color: #a5b4fc; font-size: 0.875rem;',
            }),
        }
        labels = {'content': '', 'image': 'Image (optional)'}

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('content') and not cleaned.get('image'):
            raise forms.ValidationError("A story needs either text or an image.")
        return cleaned


# =====================================================================
# Profile & account settings
# =====================================================================

class ProfileForm(forms.ModelForm):
    """Edit profile: avatar, bio, location."""

    class Meta:
        model = Profile
        fields = ('avatar', 'bio', 'location')
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Tell people about yourself...',
                'rows': 3,
                'maxlength': 300,
                'style': 'resize: vertical; font-family: inherit;',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'City, Country',
                'maxlength': 100,
            }),
            'avatar': forms.ClearableFileInput(attrs={
                'accept': 'image/*',
                'style': 'color: #a5b4fc; font-size: 0.875rem;',
            }),
        }
        labels = {'avatar': 'Profile picture', 'bio': '', 'location': ''}


class AccountForm(forms.ModelForm):
    """Edit account: email + first/last name."""

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'you@example.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last name'}),
        }
        labels = {'email': '', 'first_name': '', 'last_name': ''}