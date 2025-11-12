"""
Form Template Models for Dynamic Forms
Allows creating reusable form templates that can be used for both:
- Lead forms (agents fill, authenticated)
- Share forms (public link, anyone fills)
"""
from django.db import models
from django.utils.crypto import get_random_string
from products.models import Product


class FormTemplate(models.Model):
    """
    Defines the structure of a form (which fields, validation rules, etc.)
    Can be used for both agent lead creation and public sharing
    """
    # Basic info
    title = models.CharField(
        max_length=200,
        help_text="e.g., 'Life Insurance Application Form'"
    )
    description = models.TextField(
        blank=True,
        help_text="Instructions for filling the form"
    )

    # Product association (optional - forms can be product-specific or generic)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='form_templates',
        help_text="If set, this form is for a specific product"
    )

    # Form schema - defines fields, validation, UI hints
    # Example structure:
    # {
    #   "fields": [
    #     {
    #       "name": "customer_name",
    #       "label": "Full Name",
    #       "type": "text",
    #       "required": true,
    #       "placeholder": "Enter full name"
    #     },
    #     {
    #       "name": "email",
    #       "label": "Email Address",
    #       "type": "email",
    #       "required": true,
    #       "validation": {"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}
    #     },
    #     {
    #       "name": "phone",
    #       "label": "Phone Number",
    #       "type": "phone",
    #       "required": true
    #     },
    #     {
    #       "name": "coverage_amount",
    #       "label": "Coverage Amount",
    #       "type": "number",
    #       "required": true,
    #       "suffix": "₹"
    #     }
    #   ]
    # }
    schema = models.JSONField(
        help_text="Form field definitions (JSON structure)"
    )

    # Share settings
    is_shareable = models.BooleanField(
        default=False,
        help_text="Can this form be shared via public link?"
    )
    share_token = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        help_text="Unique token for public access (e.g., /forms/share/abc123xyz)"
    )
    share_expiry = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional expiry for share link"
    )

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leads_formtemplate'
        verbose_name = 'Form Template'
        verbose_name_plural = 'Form Templates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['share_token']),
            models.Index(fields=['product', 'is_active']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate share token if form is shareable
        if self.is_shareable and not self.share_token:
            self.share_token = get_random_string(32)
        super().save(*args, **kwargs)

    @property
    def share_url(self):
        """Get the public share URL for this form"""
        if self.is_shareable and self.share_token:
            return f"/forms/share/{self.share_token}"
        return None
