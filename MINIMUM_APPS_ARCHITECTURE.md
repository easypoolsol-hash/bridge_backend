# Minimum Django Apps Architecture - Bare Essentials

## 🎯 **3 Core Apps (Bare Minimum)**

For a working platform, you need **only 3 Django apps**:

```
bridge/backend_bridge/app/
├── core/                    # Django project settings (already exists)
├── accounts/               # ✅ App 1: Users & Authentication
├── products/               # ✅ App 2: Products & Categories
└── leads/                  # ✅ App 3: Lead Management & Forms
```

---

## 📦 **App 1: `accounts/` - Users & Authentication**

### **Purpose:**
- Handle user registration and login
- Firebase authentication integration
- User roles (superuser, admin, agent)
- Admin group permissions

### **Models:**
```python
# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Extended User model"""
    USER_TYPES = [
        ('superuser', 'Super User'),
        ('admin', 'Admin'),
        ('agent', 'Agent'),
    ]

    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='agent')
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    # Will be linked to Agent model if user_type is 'agent'


class Agent(models.Model):
    """Agent profile - only for users with user_type='agent'"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    agent_code = models.CharField(max_length=20, unique=True)
    referral_link = models.CharField(max_length=200)

    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)  # %
    status = models.CharField(max_length=20, default='active')  # active/inactive/suspended

    # KYC
    kyc_verified = models.BooleanField(default=False)
    kyc_documents = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.agent_code} - {self.user.get_full_name()}"
```

### **API Endpoints:**
```
POST   /api/auth/register/              # Register new user
POST   /api/auth/login/                 # Login (Firebase token → JWT)
POST   /api/auth/verify-token/          # Verify Firebase token
GET    /api/auth/me/                    # Get current user info
PATCH  /api/agents/profile/             # Update agent profile
```

---

## 📦 **App 2: `products/` - Products & Categories**

### **Purpose:**
- Manage product categories (Life, Health, Loans, etc.)
- Manage products (specific insurance plans, loan products)
- Store commission rates
- Track product providers

### **Models:**
```python
# products/models.py

from django.db import models

class ProductCategory(models.Model):
    """Main categories: Life Insurance, Health Insurance, Loans, etc."""
    CATEGORY_TYPES = [
        ('life_insurance', 'Life Insurance'),
        ('health_insurance', 'Health Insurance'),
        ('credit_card', 'Credit Card'),
        ('loan', 'Loan'),
        ('mutual_fund', 'Mutual Fund'),
        ('equity', 'Equity'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    category_type = models.CharField(max_length=50, choices=CATEGORY_TYPES, unique=True)
    icon = models.CharField(max_length=50, blank=True)  # Icon name for Flutter
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProductProvider(models.Model):
    """Insurance companies, banks, financial institutions"""
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=50)  # insurance_company, bank, nbfc
    logo_url = models.URLField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Specific products: HDFC Term Life, SBI Home Loan, etc."""
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products')
    provider = models.ForeignKey(ProductProvider, on_delete=models.PROTECT, related_name='products')

    name = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField(blank=True)

    # Commission
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)  # percentage
    commission_type = models.CharField(max_length=20, default='percentage')  # percentage/flat

    # Status
    active = models.BooleanField(default=True)

    # Form configuration (optional - for dynamic forms)
    form_fields = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['category', 'slug']

    def __str__(self):
        return f"{self.provider.name} - {self.name}"
```

### **API Endpoints:**
```
GET    /api/products/categories/        # List all categories
GET    /api/products/                   # List products (filter by category)
GET    /api/products/{id}/              # Get product details
```

---

## 📦 **App 3: `leads/` - Lead Management & Forms**

### **Purpose:**
- Store lead submissions from agents
- Handle all form types (flexible JSON storage)
- Track lead status
- Store documents/attachments

### **Models:**
```python
# leads/models.py

from django.db import models
from accounts.models import User, Agent
from products.models import Product

class Lead(models.Model):
    """Main lead model - handles ALL product types"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('in_progress', 'In Progress'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('converted', 'Converted'),
    ]

    # Reference
    reference_number = models.CharField(max_length=50, unique=True)  # LI-2025-123

    # Relations
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='leads')

    # Lead info
    customer_name = models.CharField(max_length=200)  # For quick reference
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)

    # Form data - FLEXIBLE JSON storage (handles ANY form)
    form_data = models.JSONField()  # Stores complete form submission

    # Metadata
    source = models.CharField(max_length=50, default='mobile_app')  # mobile_app/web/referral
    referral_code = models.CharField(max_length=50, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')

    # Assignment (for admin processing)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    converted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference_number} - {self.customer_name}"

    def save(self, *args, **kwargs):
        # Auto-generate reference number
        if not self.reference_number:
            prefix = self.product.category.category_type[:2].upper()
            from django.utils import timezone
            year = timezone.now().year
            # Simple counter - in production use atomic operations
            count = Lead.objects.filter(created_at__year=year).count() + 1
            self.reference_number = f"{prefix}-{year}-{count}"

        super().save(*args, **kwargs)


class LeadDocument(models.Model):
    """Documents attached to leads (KYC, medical reports, etc.)"""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='documents')

    document_type = models.CharField(max_length=50)  # id_proof, address_proof, medical
    file = models.FileField(upload_to='lead_documents/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField()  # bytes

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead.reference_number} - {self.document_type}"


class LeadActivity(models.Model):
    """Activity log for each lead (timeline)"""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    activity_type = models.CharField(max_length=50)  # status_change, note, document_upload
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
```

### **API Endpoints:**
```
POST   /api/leads/                      # Create new lead (any product type)
GET    /api/leads/                      # List leads (for agent/admin)
GET    /api/leads/{id}/                 # Get lead details
PATCH  /api/leads/{id}/                 # Update lead status
POST   /api/leads/{id}/documents/       # Upload document
GET    /api/leads/{id}/activities/      # Get lead timeline
```

---

## 🎯 **Why Only 3 Apps?**

### **1. `accounts/` handles:**
- ✅ User authentication (Firebase + Django)
- ✅ User roles (superuser, admin, agent)
- ✅ Agent profiles
- ✅ Permissions

### **2. `products/` handles:**
- ✅ All product categories
- ✅ All products (insurance, loans, credit cards, etc.)
- ✅ Providers
- ✅ Commission structure

### **3. `leads/` handles:**
- ✅ ALL form submissions (flexible JSON)
- ✅ Lead tracking
- ✅ Documents
- ✅ Status management
- ✅ Activity timeline

---

## 📊 **Database Tables Summary**

```
accounts_user              → Users (superuser, admin, agent)
accounts_agent             → Agent profiles
auth_group                 → Admin groups (built-in Django)
auth_permission            → Permissions (built-in Django)

products_productcategory   → Life, Health, Loans, etc.
products_productprovider   → HDFC, SBI, ICICI, etc.
products_product           → Specific products

leads_lead                 → All lead submissions
leads_leaddocument         → Uploaded documents
leads_leadactivity         → Activity timeline
```

**Total: ~9 tables** (minimal and clean!)

---

## 🔧 **Admin Group Examples**

Using Django's built-in `Group` model:

```python
# Create admin groups
from django.contrib.auth.models import Group, Permission

# 1. Product Admin
product_admin_group = Group.objects.create(name='Product Admin')
product_admin_group.permissions.add(
    # Can manage products
    Permission.objects.get(codename='add_product'),
    Permission.objects.get(codename='change_product'),
    Permission.objects.get(codename='view_product'),
)

# 2. Lead Manager
lead_manager_group = Group.objects.create(name='Lead Manager')
lead_manager_group.permissions.add(
    # Can view and update leads
    Permission.objects.get(codename='view_lead'),
    Permission.objects.get(codename='change_lead'),
)

# 3. Agent Manager
agent_manager_group = Group.objects.create(name='Agent Manager')
agent_manager_group.permissions.add(
    # Can manage agents
    Permission.objects.get(codename='add_agent'),
    Permission.objects.get(codename='change_agent'),
    Permission.objects.get(codename='view_agent'),
)
```

---

## ✅ **Benefits of This Structure**

1. **Simple**: Only 3 apps to manage
2. **Flexible**: JSON fields handle any form type
3. **Scalable**: Easy to add new product types
4. **Clean**: No redundant models
5. **Standard**: Uses Django best practices
6. **Maintainable**: Easy to understand and modify

---

## 🚀 **What's Next?**

After creating these 3 apps, you need:
1. Install Django REST Framework
2. Create serializers for each model
3. Create API views
4. Set up Firebase authentication
5. Generate OpenAPI spec
6. Configure Django admin

**Should I proceed with creating these 3 apps?**
