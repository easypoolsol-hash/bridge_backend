from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Agent


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'user_type', 'is_active', 'created_at']
    list_filter = ['user_type', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'phone']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('firebase_uid', 'user_type', 'phone')
        }),
    )


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['agent_code', 'user', 'status', 'commission_rate', 'kyc_verified', 'created_at']
    list_filter = ['status', 'kyc_verified']
    search_fields = ['agent_code', 'user__username', 'user__email']
    readonly_fields = ['agent_code', 'referral_link', 'created_at', 'updated_at']
