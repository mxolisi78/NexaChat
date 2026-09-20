"""
Token-based authentication API for NexaChat.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    POST /api/auth/register/
    Body: { "username": "...", "email": "...", "password": "..." }
    Returns: { "token": "...", "user": {...} }
    """
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response(
            {'error': 'username and password are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'username already taken'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )
    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    Returns: { "token": "...", "user": {...} }
    """
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {'error': 'invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    POST /api/auth/logout/
    Deletes the current user's token.
    """
    try:
        request.user.auth_token.delete()
    except Token.DoesNotExist:
        pass
    return Response({'detail': 'logged out'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    GET /api/auth/me/
    Returns the current user's info (used to verify a token).
    """
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'date_joined': request.user.date_joined,
    })
