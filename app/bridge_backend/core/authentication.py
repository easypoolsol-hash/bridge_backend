"""
Firebase Authentication Backend for Bridge Backend
Following backend_easy and Google Cloud best practices
Auto-creates users on first Firebase login with zero-trust security
"""

import logging

import firebase_admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from firebase_admin import auth
from rest_framework import authentication, exceptions

logger = logging.getLogger(__name__)

User = get_user_model()


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Firebase JWT token authentication.

    Google Cloud best practice:
    - Automatically creates User objects on first login
    - Assigns to "New User" group with ZERO permissions (secure by default)
    - Admin manually promotes to appropriate role

    Usage:
        Authorization: Bearer <firebase_id_token>
    """

    def authenticate(self, request):
        """
        Authenticate user with Firebase ID token.

        Returns:
            (user, None) if authentication successful
            None if no token provided

        Raises:
            AuthenticationFailed if token is invalid
        """
        auth_header = request.META.get("HTTP_AUTHORIZATION")

        if not auth_header:
            return None

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            # Verify Firebase ID token
            decoded_token = auth.verify_id_token(token)
            firebase_uid = decoded_token["uid"]
            email = decoded_token.get("email", "")
            name = decoded_token.get("name", "")

            # Auto-create user on first login (Zero-Trust pattern)
            user, created = User.objects.get_or_create(
                firebase_uid=firebase_uid,
                defaults={
                    "username": email.split("@")[0] if email else firebase_uid[:30],
                    "email": email,
                    "first_name": name.split(" ")[0] if name else "",
                    "last_name": " ".join(name.split(" ")[1:]) if name and len(name.split(" ")) > 1 else "",
                    "user_type": "agent",  # Default user type
                },
            )

            if created:
                # Secure by default: Assign to "New User" group (NO permissions)
                new_user_group, _ = Group.objects.get_or_create(name="New User")
                user.groups.add(new_user_group)

                logger.info(
                    f"✅ Auto-created user from Firebase: {firebase_uid} "
                    f"(email: {email}) - assigned 'New User' group"
                )

            # Update last login (Django doesn't do this for custom auth backends)
            from django.utils import timezone
            from datetime import timedelta

            now = timezone.now()
            # Throttle: Only update if last login > 5 minutes ago (reduce DB writes)
            should_update = user.last_login is None or (now - user.last_login) > timedelta(minutes=5)

            if should_update:
                user.last_login = now
                user.save(update_fields=["last_login"])

            return (user, None)

        except auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid Firebase token: {e}")
            raise exceptions.AuthenticationFailed("Invalid Firebase token")

        except auth.ExpiredIdTokenError as e:
            logger.warning(f"Expired Firebase token: {e}")
            raise exceptions.AuthenticationFailed("Firebase token expired")

        except Exception as e:
            logger.error(f"Firebase authentication error: {e}")
            raise exceptions.AuthenticationFailed("Authentication failed")

    def authenticate_header(self, request):
        """
        Return WWW-Authenticate header for 401 responses.
        """
        return "Bearer realm=firebase"
