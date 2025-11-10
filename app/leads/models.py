from django.db import models
from django.utils import timezone
from accounts.models import User, Agent
from products.models import Product


class Lead(models.Model):
    """
    Main lead model - handles ALL product types with flexible JSON storage
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('in_progress', 'In Progress'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('converted', 'Converted'),
    ]

    # Reference number (auto-generated)
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="e.g., LI-2025-123"
    )

    # Relations
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='leads'
    )
    agent = models.ForeignKey(
        Agent,
        on_delete=models.PROTECT,
        related_name='leads'
    )

    # Quick reference fields (duplicated from form_data for easy querying)
    customer_name = models.CharField(max_length=200, help_text="For quick reference")
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)

    # FLEXIBLE FORM DATA - stores any form structure
    form_data = models.JSONField(
        help_text="Complete form submission data (flexible structure)"
    )

    # Metadata
    source = models.CharField(
        max_length=50,
        default='mobile_app',
        help_text="mobile_app, web, referral"
    )
    referral_code = models.CharField(max_length=50, blank=True)

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted'
    )

    # Assignment (for admin processing)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads',
        help_text="Admin user assigned to process this lead"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    converted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'leads_lead'
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference_number']),
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.reference_number} - {self.customer_name}"

    def save(self, *args, **kwargs):
        # Auto-generate reference number
        if not self.reference_number:
            # Get sub-category slug prefix (e.g., "life-insurance" → "LI")
            sub_cat_name = self.product.sub_category.name
            prefix = ''.join([word[0].upper() for word in sub_cat_name.split()[:2]])

            year = timezone.now().year

            # Count leads for this year (in production, use atomic counter)
            count = Lead.objects.filter(created_at__year=year).count() + 1

            self.reference_number = f"{prefix}-{year}-{count}"

        super().save(*args, **kwargs)


class LeadDocument(models.Model):
    """
    Documents attached to leads (KYC, medical reports, income proof, etc.)
    """
    DOCUMENT_TYPES = [
        ('id_proof', 'ID Proof'),
        ('address_proof', 'Address Proof'),
        ('income_proof', 'Income Proof'),
        ('medical_report', 'Medical Report'),
        ('other', 'Other'),
    ]

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='lead_documents/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    content_type = models.CharField(max_length=100, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'leads_leaddocument'
        verbose_name = 'Lead Document'
        verbose_name_plural = 'Lead Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.lead.reference_number} - {self.document_type}"


class LeadActivity(models.Model):
    """
    Activity log / timeline for each lead
    Tracks status changes, notes, document uploads, etc.
    """
    ACTIVITY_TYPES = [
        ('created', 'Lead Created'),
        ('status_change', 'Status Changed'),
        ('note_added', 'Note Added'),
        ('document_uploaded', 'Document Uploaded'),
        ('assigned', 'Assigned to User'),
        ('contacted', 'Customer Contacted'),
    ]

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who performed this activity"
    )

    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField()

    # Extra metadata (old_status, new_status, etc.)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'leads_leadactivity'
        verbose_name = 'Lead Activity'
        verbose_name_plural = 'Lead Activities'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.lead.reference_number} - {self.activity_type}"
