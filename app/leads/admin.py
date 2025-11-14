from django.contrib import admin
from .models import Lead, LeadDocument, LeadActivity, Client
from .models_forms import FormTemplate


class LeadDocumentInline(admin.TabularInline):
    model = LeadDocument
    extra = 0
    readonly_fields = ['filename', 'file_size', 'uploaded_at']


class LeadActivityInline(admin.TabularInline):
    model = LeadActivity
    extra = 0
    readonly_fields = ['activity_type', 'description', 'user', 'created_at']


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Client Information', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'customer_name', 'client', 'product', 'agent', 'status', 'pdf_link', 'created_at']
    list_filter = ['status', 'product__sub_category__main_category', 'product__sub_category', 'created_at']
    search_fields = ['reference_number', 'customer_name', 'customer_email', 'customer_phone', 'client__name', 'client__phone']
    readonly_fields = ['reference_number', 'client', 'pdf_download_link', 'created_at', 'updated_at']

    fieldsets = (
        ('Lead Information', {
            'fields': ('reference_number', 'product', 'agent', 'status')
        }),
        ('Client Information', {
            'fields': ('client',),
            'description': 'Auto-assigned client (Google-style ID)'
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Form Data', {
            'fields': ('form_data',),
            'classes': ('collapse',)
        }),
        ('PDF Document', {
            'fields': ('pdf_download_link',),
            'description': 'Auto-generated PDF (created on form submission)'
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
        ('Metadata', {
            'fields': ('source', 'referral_code', 'created_at', 'updated_at', 'converted_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [LeadDocumentInline, LeadActivityInline]

    def pdf_link(self, obj):
        """Show PDF download link in list view"""
        if obj.pdf_file:
            return f'<a href="{obj.pdf_file.url}" target="_blank">Download PDF</a>'
        return "No PDF"
    pdf_link.short_description = 'PDF'
    pdf_link.allow_tags = True

    def pdf_download_link(self, obj):
        """Show PDF download link in detail view"""
        if obj.pdf_file:
            return f'<a href="{obj.pdf_file.url}" target="_blank" class="button">Download PDF</a>'
        return "PDF not available"
    pdf_download_link.short_description = 'PDF Document'
    pdf_download_link.allow_tags = True


@admin.register(LeadDocument)
class LeadDocumentAdmin(admin.ModelAdmin):
    list_display = ['lead', 'document_type', 'filename', 'file_size', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['lead__reference_number', 'filename']
    readonly_fields = ['uploaded_at']


@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ['lead', 'activity_type', 'user', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['lead__reference_number', 'description']
    readonly_fields = ['created_at']


@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'product', 'is_shareable', 'is_active', 'created_at']
    list_filter = ['is_shareable', 'is_active', 'product']
    search_fields = ['title', 'description']
    readonly_fields = ['share_token', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'product')
        }),
        ('Form Schema', {
            'fields': ('schema',),
            'description': 'JSON schema defining form fields and validation'
        }),
        ('Sharing Settings', {
            'fields': ('is_shareable', 'share_token', 'share_expiry')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
