"""
Leads API Permissions
Following Google/Fortune 500 zero-trust security model
"""

from rest_framework import permissions


class IsAgentOwner(permissions.BasePermission):
    """
    Permission: Agents can only access their own leads
    Admins/Staff can access all leads

    Zero-trust principle: Agent isolation for data security
    """

    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user owns the lead or is admin"""
        # Admins can access all leads
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Agent users can only access their own leads
        if hasattr(request.user, "agent_profile"):
            return obj.agent == request.user.agent_profile

        # If user has no agent profile, deny access
        return False
