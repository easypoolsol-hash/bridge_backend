from django.contrib import admin
from .models import Lead, LeadDocument, LeadActivity
from .models_forms import FormTemplate


class LeadDocumentInline(admin.TabularInline):
    model = LeadDocument
    extra = 0
    readonly_fields = ['filename', 'file_size', 'uploaded_at']


class LeadActivityInline(admin.TabularInline):
    model = LeadActivity
    extra = 0
    readonly_fields = ['activity_type', 'description', 'user', 'created_at']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'customer_name', 'product', 'agent', 'status', 'created_at']
    list_filter = ['status', 'product__sub_category__main_category', 'product__sub_category', 'created_at']
    search_fields = ['reference_number', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['reference_number', 'created_at', 'updated_at']

    fieldsets = (
        ('Lead Information', {
            'fields': ('reference_number', 'product', 'agent', 'status')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Form Data', {
            'fields': ('form_data',),
            'classes': ('collapse',)
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
