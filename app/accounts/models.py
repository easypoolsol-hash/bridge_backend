from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    Handles authentication for superusers, admins, and agents
    """
    USER_TYPES = [
        ('superuser', 'Super User'),
        ('admin', 'Admin'),
        ('agent', 'Agent'),
    ]

    # Firebase integration
    firebase_uid = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        help_text="Firebase User ID"
    )

    # User classification
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='agent'
    )

    # Additional fields
    phone = models.CharField(max_length=20, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.user_type})"


class Agent(models.Model):
    """
    Agent profile - linked to User model
    Contains agent-specific information and referral details
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='agent_profile'
    )

    # Agent identification
    agent_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique agent code (e.g., AGT001)"
    )

    referral_link = models.CharField(
        max_length=200,
        help_text="Agent's unique referral link"
    )

    # Commission
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.0,
        help_text="Default commission percentage"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # KYC (Know Your Customer)
    kyc_verified = models.BooleanField(default=False)
    kyc_documents = models.JSONField(
        default=dict,
        blank=True,
        help_text="Store KYC document info as JSON"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_agent'
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'

    def __str__(self):
        return f"{self.agent_code} - {self.user.get_full_name()}"

    def save(self, *args, **kwargs):
        # Auto-generate agent code if not provided
        if not self.agent_code:
            last_agent = Agent.objects.order_by('-id').first()
            if last_agent:
                last_num = int(last_agent.agent_code.replace('AGT', ''))
                new_num = last_num + 1
            else:
                new_num = 1
            self.agent_code = f"AGT{new_num:04d}"

        # Auto-generate referral link
        if not self.referral_link:
            self.referral_link = f"https://easypool.app/ref/{self.agent_code}"

        super().save(*args, **kwargs)
