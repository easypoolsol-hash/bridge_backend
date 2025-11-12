"""
Authentication API viewsets following Google Cloud API Design Guide.
Resource-oriented design with standard methods and custom methods.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class AuthViewSet(viewsets.ViewSet):
    """
    User authentication and profile management.

    Following Google Cloud API Design Guide:
    - Resource: users/me (current authenticated user)
    - Standard method: GET users/me (retrieve profile)
    - Custom method: POST users/me:sync (sync with Firebase)

    All endpoints require Firebase authentication token.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='users_me_sync',
        summary='Sync authenticated user',
        description=(
            'Custom method to sync user with backend after Firebase authentication. '
            'Triggers auto-creation on first login if user doesn\'t exist. '
            'Google Cloud pattern: POST /users/me:sync'
        ),
        tags=['Users'],
    )
    @action(detail=False, methods=['post'], url_path='me/sync', url_name='me-sync')
    def sync_me(self, request):
        """
        Sync current user with backend (POST /users/me:sync).

        Custom method following Google Cloud API pattern for non-standard operations.
        The colon (:) indicates a custom method on the resource.

        Auto-creates user on first Firebase login with:
        - firebase_uid from token
        - email, name from Firebase
        - user_type: 'agent' (default)
        - groups: ['New User'] (zero permissions - secure by default)
        """
        user = request.user

        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'user_type': user.user_type,
                'groups': [group.name for group in user.groups.all()],
                'is_active': user.is_active,
            },
            'message': 'User synced successfully',
        }, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id='users_me_get',
        summary='Get authenticated user profile',
        description=(
            'Standard GET method to retrieve current user profile. '
            'Google Cloud pattern: GET /users/me'
        ),
        tags=['Users'],
    )
    @action(detail=False, methods=['get'], url_path='me', url_name='me')
    def get_me(self, request):
        """
        Get current user profile (GET /users/me).

        Standard method following Google Cloud API pattern.
        Uses 'me' as alias for current authenticated user's ID.
        """
        user = request.user

        return Response({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
            'groups': [group.name for group in user.groups.all()],
            'is_active': user.is_active,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None,
        }, status=status.HTTP_200_OK)
