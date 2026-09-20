"""
Tests for the NexaChat chat app.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from .models import ChatRoom, Message


# =====================================================================
# Model tests
# =====================================================================

class ChatRoomModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='alice', password='testpass123'
        )

    def test_slug_auto_generated_from_name(self):
        """Saving a room auto-populates the slug from the name."""
        room = ChatRoom.objects.create(
            name='General Discussion',
            created_by=self.user,
        )
        self.assertEqual(room.slug, 'general-discussion')

    def test_slug_preserved_if_provided(self):
        """Explicit slug is not overwritten."""
        room = ChatRoom.objects.create(
            name='General',
            slug='custom-slug',
            created_by=self.user,
        )
        self.assertEqual(room.slug, 'custom-slug')

    def test_str_returns_name(self):
        room = ChatRoom.objects.create(name='Random', created_by=self.user)
        self.assertEqual(str(room), 'Random')

    def test_ordering_newest_first(self):
        """Rooms are ordered newest-first by default."""
        room1 = ChatRoom.objects.create(name='First', created_by=self.user)
        room2 = ChatRoom.objects.create(name='Second', created_by=self.user)
        rooms = list(ChatRoom.objects.all())
        self.assertEqual(rooms[0], room2)
        self.assertEqual(rooms[1], room1)


class MessageModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='bob', password='testpass123'
        )
        self.room = ChatRoom.objects.create(
            name='Test Room',
            created_by=self.user,
        )

    def test_message_str(self):
        msg = Message.objects.create(
            room=self.room,
            author=self.user,
            content='Hello world',
        )
        self.assertIn('bob', str(msg))
        self.assertIn('Hello world', str(msg))

    def test_ordering_oldest_first(self):
        """Messages are ordered oldest-first (chat convention)."""
        m1 = Message.objects.create(room=self.room, author=self.user, content='first')
        m2 = Message.objects.create(room=self.room, author=self.user, content='second')
        messages = list(Message.objects.all())
        self.assertEqual(messages[0], m1)
        self.assertEqual(messages[1], m2)

    def test_cascade_delete_on_room(self):
        """Deleting a room deletes its messages."""
        Message.objects.create(room=self.room, author=self.user, content='hi')
        self.assertEqual(Message.objects.count(), 1)
        self.room.delete()
        self.assertEqual(Message.objects.count(), 0)


# =====================================================================
# View (HTTP) tests
# =====================================================================

class HomeViewTests(TestCase):

    def test_home_renders_for_anonymous(self):
        response = self.client.get(reverse('chat:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'NexaChat')


class RoomListAuthTests(TestCase):

    def test_room_list_redirects_anonymous_to_login(self):
        response = self.client.get(reverse('chat:room_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_room_list_shows_logged_in(self):
        user = User.objects.create_user(username='carol', password='pass12345')
        self.client.login(username='carol', password='pass12345')
        ChatRoom.objects.create(name='Test', created_by=user)

        response = self.client.get(reverse('chat:room_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test')


class RoomDetailTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='dave', password='pass12345')
        self.room = ChatRoom.objects.create(
            name='Room Detail',
            description='For testing',
            created_by=self.user,
        )
        self.client.login(username='dave', password='pass12345')

    def test_room_detail_get(self):
        response = self.client.get(reverse('chat:room_detail', args=[self.room.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Room Detail')

    def test_room_detail_post_creates_message(self):
        response = self.client.post(
            reverse('chat:room_detail', args=[self.room.slug]),
            {'content': 'Hello from test!'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Message.objects.count(), 1)
        msg = Message.objects.first()
        self.assertEqual(msg.content, 'Hello from test!')
        self.assertEqual(msg.author, self.user)
        self.assertEqual(msg.room, self.room)

    def test_room_detail_post_ignores_empty(self):
        self.client.post(
            reverse('chat:room_detail', args=[self.room.slug]),
            {'content': ''},
        )
        self.assertEqual(Message.objects.count(), 0)


# =====================================================================
# API tests
# =====================================================================

class AuthAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user_and_returns_token(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'safepassword123',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('token', response.data)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_rejects_duplicate_username(self):
        User.objects.create_user(username='dup', password='pass12345')
        response = self.client.post('/api/auth/register/', {
            'username': 'dup',
            'password': 'anotherpass123',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register_requires_username_and_password(self):
        response = self.client.post('/api/auth/register/', {
            'email': 'only@example.com',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_login_returns_token(self):
        User.objects.create_user(username='login', password='pass12345')
        response = self.client.post('/api/auth/login/', {
            'username': 'login',
            'password': 'pass12345',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)

    def test_login_rejects_bad_credentials(self):
        User.objects.create_user(username='login2', password='pass12345')
        response = self.client.post('/api/auth/login/', {
            'username': 'login2',
            'password': 'wrong',
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_me_requires_auth(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 401)

    def test_me_returns_user_with_token(self):
        user = User.objects.create_user(username='me', password='pass12345')
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'me')


class RoomsAPITests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='api', password='pass12345')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_rooms_list_requires_auth(self):
        anon = APIClient()
        response = anon.get('/api/rooms/')
        self.assertEqual(response.status_code, 401)

    def test_rooms_list_with_token(self):
        ChatRoom.objects.create(name='Visible', created_by=self.user)
        response = self.client.get('/api/rooms/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Visible')

    def test_rooms_create_via_api(self):
        response = self.client.post('/api/rooms/', {
            'name': 'API Room',
            'description': 'Created through REST',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ChatRoom.objects.filter(name='API Room').exists())

    def test_message_create_via_api(self):
        room = ChatRoom.objects.create(name='Room1', created_by=self.user)
        response = self.client.post(
            f'/api/rooms/{room.slug}/messages/',
            {'content': 'API message!'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.objects.count(), 1)

    def test_message_list_via_api(self):
        room = ChatRoom.objects.create(name='Room2', created_by=self.user)
        Message.objects.create(room=room, author=self.user, content='first')
        Message.objects.create(room=room, author=self.user, content='second')

        response = self.client.get(f'/api/rooms/{room.slug}/messages/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['content'], 'first')
