from django.db import models
from django.utils.text import slugify


class MainCategory(models.Model):
    """
    Main product categories: Insurance, Loans, Credit Cards, Investments
    """
    name = models.CharField(max_length=100, help_text="e.g., Insurance, Loans")
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name for Flutter")
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products_maincategory'
        verbose_name = 'Main Category'
        verbose_name_plural = 'Main Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class SubCategory(models.Model):
    """
    Sub-categories: Life Insurance, Health Insurance, Car Insurance,
    Home Loan, Personal Loan, Mutual Funds, etc.
    """
    main_category = models.ForeignKey(
        MainCategory,
        on_delete=models.CASCADE,
        related_name='sub_categories'
    )

    name = models.CharField(max_length=100, help_text="e.g., Life Insurance, Car Insurance")
    slug = models.SlugField()
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name for Flutter")
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    # Form template for this sub-category (optional)
    form_template = models.JSONField(
        default=dict,
        blank=True,
        help_text="Default form fields for products in this sub-category"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products_subcategory'
        verbose_name = 'Sub Category'
        verbose_name_plural = 'Sub Categories'
        ordering = ['main_category', 'display_order', 'name']
        unique_together = ['main_category', 'slug']

    def __str__(self):
        return f"{self.main_category.name} → {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Actual products: HDFC Term Life, SBI Home Loan, etc.
    Provider info can be embedded in form_data or custom_fields
    """
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        related_name='products'
    )

    name = models.CharField(max_length=200, help_text="e.g., Term Life Plan, Home Loan Premium")
    slug = models.SlugField()
    description = models.TextField(blank=True)

    # Features/Benefits (stored as JSON array)
    key_features = models.JSONField(
        default=list,
        blank=True,
        help_text="List of key features/benefits"
    )

    # Commission
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Commission percentage"
    )
    commission_type = models.CharField(
        max_length=20,
        default='percentage',
        choices=[
            ('percentage', 'Percentage'),
            ('flat', 'Flat Amount'),
        ]
    )

    # Product-specific customizations
    # Provider info can go here: {"provider": "HDFC", "provider_logo": "url"}
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom product info (provider, terms, etc.)"
    )

    # Custom form fields (if different from sub-category default)
    custom_form_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text="Override sub-category form template"
    )

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products_product'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['sub_category', 'name']
        unique_together = ['sub_category', 'slug']

    def __str__(self):
        provider = self.custom_fields.get('provider', '')
        if provider:
            return f"{provider} - {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
