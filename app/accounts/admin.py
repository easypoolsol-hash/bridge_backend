from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import Agent, User

# Unregister default Group admin
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    """
    Read-only Group admin following Google Cloud IAM best practices.

    Groups should ONLY be modified via management commands (version control).
    This prevents accidental permission changes and ensures audit trail.

    To modify groups: Update seed_groups.py and run 'python manage.py seed_groups'
    """

    def has_add_permission(self, request):
        """Prevent creating groups via admin panel"""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modifying groups via admin panel"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting groups via admin panel"""
        return False

    list_display = ["name", "get_permission_count"]

    def get_permission_count(self, obj):
        """Show number of permissions assigned to group"""
        return obj.permissions.count()

    get_permission_count.short_description = "Permissions"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    User admin with group (role) management.

    Admins can:
    - Assign users to groups (promote to Agent, Admin, etc.)
    - View user information
    - Cannot modify the groups themselves (IAM pattern)
    """

    list_display = ["username", "email", "user_type", "get_groups", "is_active", "last_login"]
    list_filter = ["groups", "user_type", "is_active", "is_staff"]
    search_fields = ["username", "email", "phone", "firebase_uid"]

    def get_groups(self, obj):
        """Display groups (roles) for user"""
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
        (
            "Groups & Permissions",
            {
                "fields": ("groups",),
                "description": "Assign user to groups. To promote user to Agent, add them to 'Agent' group.",
            },
        ),
    )


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['agent_code', 'user', 'status', 'commission_rate', 'kyc_verified', 'created_at']
    list_filter = ['status', 'kyc_verified']
    search_fields = ['agent_code', 'user__username', 'user__email']
    readonly_fields = ['agent_code', 'referral_link', 'created_at', 'updated_at']
