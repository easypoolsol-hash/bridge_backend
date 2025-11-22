from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden

from .models import Agent, User

# Unregister default Group admin
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    """
    Group admin with superuser-only management.

    Only superusers can add, modify, or delete groups.
    Regular admins can only view groups.
    """

    def has_add_permission(self, request):
        """Only superusers can create groups"""
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """Only superusers can modify groups"""
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete groups"""
        return request.user.is_superuser

    list_display = ["name", "get_permission_count"]

    def get_permission_count(self, obj):
        return obj.permissions.count()

    get_permission_count.short_description = "Permissions"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    User admin with group (role) management.

    Admins can:
    - Assign users to groups (promote to Agent, Admin, etc.)
    - View and edit user information
    - Change their own password

    Only superusers can:
    - Change other users' passwords
    """

    list_display = ["username", "email", "user_type", "get_groups", "is_active", "last_login"]
    list_filter = ["groups", "user_type", "is_active", "is_staff"]
    search_fields = ["username", "email", "phone", "firebase_uid"]

    def get_groups(self, obj):
        groups = list(obj.groups.values_list("name", flat=True))
        return ", ".join(groups) if groups else "No groups"

    get_groups.short_description = "Groups (Roles)"

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Custom Fields",
            {
                "fields": ("firebase_uid", "user_type", "phone"),
            },
        ),
    )

    def user_change_password(self, request, id, form_url=''):
        """
        Only superusers can change other users' passwords.
        Users can always change their own password.
        """
        user = self.get_object(request, unquote(id))

        if user is None:
            return self._get_obj_does_not_exist_redirect(request, self.opts, id)

        # Allow users to change their own password
        # Only superusers can change other users' passwords
        if not request.user.is_superuser and user.pk != request.user.pk:
            return HttpResponseForbidden(
                "Permission denied: Only superusers can change other users' passwords."
            )

        return super().user_change_password(request, id, form_url)


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['agent_code', 'user', 'status', 'commission_rate', 'kyc_verified', 'created_at']
    list_filter = ['status', 'kyc_verified']
    search_fields = ['agent_code', 'user__username', 'user__email']
    readonly_fields = ['agent_code', 'referral_link', 'created_at', 'updated_at']
