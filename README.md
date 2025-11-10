# Bridge Backend - Insurance & Financial Products Platform

Django backend for the EasyPool insurance bridge platform.

## ✅ What's Been Created

### Django Apps (3 minimum apps)

```
app/
├── accounts/          # Users, Agents, Authentication
├── products/          # Product categories & products
└── leads/             # Lead management & form submissions
```

### Database Structure

#### **accounts app:**
- `User` - Custom user model (superuser, admin, agent) with Firebase integration
- `Agent` - Agent profiles with referral links and KYC

#### **products app:**
- `MainCategory` - Insurance, Loans, Credit Cards, Investments
- `SubCategory` - Life Insurance, Health Insurance, Car, Home Loan, etc.
- `Product` - Specific products (HDFC Term Life, SBI Home Loan)

#### **leads app:**
- `Lead` - All form submissions (flexible JSON storage)
- `LeadDocument` - Attached documents
- `LeadActivity` - Activity timeline/log

---

## 🏗️ Product Hierarchy

```
Insurance (Main Category)
  ├── Life Insurance (Sub Category)
  │   ├── HDFC Term Life (Product)
  │   └── LIC Jeevan Anand (Product)
  │
  ├── Health Insurance (Sub Category)
  │   └── Star Health Family (Product)
  │
  └── Car Insurance (Sub Category)

Loans (Main Category)
  ├── Home Loan (Sub Category)
  │   └── SBI Home Loan (Product)
  │
  └── Personal Loan (Sub Category)
```

---

## 📝 Form Data Handling

**Forms are defined in Flutter frontend** - Backend stores flexible JSON:

```python
# Example Lead with Life Insurance form
lead = Lead.objects.create(
    product=hdfc_term_life,
    agent=agent,
    customer_name="Rahul Kumar",
    form_data={
        "full_name": "Rahul Kumar",
        "age": 30,
        "coverage_amount": 1000000,
        "smoker": False,
        "medical_history": "None"
        # Can store ANY fields!
    }
)
```

**Provider info** is embedded in Product.custom_fields:
```python
product.custom_fields = {
    "provider": "HDFC",
    "provider_logo": "https://...",
    "terms_url": "https://..."
}
```

---

## 🚀 Next Steps

### 1. Install Dependencies
```bash
pip install django djangorestframework django-cors-headers
```

### 2. Create Database
```bash
cd app
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Superuser
```bash
python manage.py createsuperuser
```

### 4. Run Server
```bash
python manage.py runserver
```

### 5. Access Admin
```
http://localhost:8000/admin/
```

---

## 📊 Example Data Setup

After migrations, you can create sample data:

```python
python manage.py shell

from products.models import MainCategory, SubCategory, Product

# Create main category
insurance = MainCategory.objects.create(
    name="Insurance",
    slug="insurance",
    icon="security"
)

# Create sub-category
life_insurance = SubCategory.objects.create(
    main_category=insurance,
    name="Life Insurance",
    slug="life-insurance"
)

# Create product
Product.objects.create(
    sub_category=life_insurance,
    name="Term Life Plan",
    slug="term-life-plan",
    commission_rate=5.5,
    custom_fields={
        "provider": "HDFC",
        "min_coverage": 500000,
        "max_coverage": 10000000
    }
)
```

---

## 🔑 Key Features

1. **Flexible Form Storage** - JSON fields handle any product form
2. **No Provider Model** - Provider info embedded in products
3. **Auto-Generated References** - Lead reference numbers (LI-2025-123)
4. **Admin Groups** - Use Django's built-in Groups for permissions
5. **Activity Tracking** - Timeline for each lead
6. **Document Uploads** - Attach KYC and other docs to leads

---

## 📂 Files Created

- `accounts/models.py` - User and Agent models
- `products/models.py` - Product hierarchy models
- `leads/models.py` - Lead management models
- `bridge_backend/settings.py` - Updated with apps and AUTH_USER_MODEL

---

## 🎯 Todo

- [ ] Install Django REST Framework
- [ ] Create serializers for all models
- [ ] Create API views and URLs
- [ ] Setup Firebase authentication
- [ ] Generate OpenAPI specification
- [ ] Configure Django admin interfaces
- [ ] Add CORS headers for Flutter
- [ ] Setup media files for document uploads

---

## 💡 Architecture Notes

- **3 apps minimum** - keeps it simple and maintainable
- **JSON fields** - maximum flexibility for forms
- **No separate form builder app** - forms defined in Flutter
- **Provider info in product** - no separate provider model
- **Standard Django patterns** - easy to understand and extend
