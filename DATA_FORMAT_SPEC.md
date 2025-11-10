# Data Format Specification: Flutter Frontend ↔ Django Backend

## Overview
This document defines the exact data format for communication between Flutter frontend and Django backend.

---

## 🔐 Authentication Flow

### 1. User Login (Firebase → Django)

**Flutter sends:**
```json
POST /api/auth/verify-token/
{
  "firebase_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij...",
  "device_info": {
    "platform": "android",
    "version": "1.0.0",
    "device_id": "abc123"
  }
}
```

**Django responds:**
```json
{
  "success": true,
  "user": {
    "id": 123,
    "firebase_uid": "abc123xyz",
    "email": "agent@example.com",
    "user_type": "agent",
    "agent": {
      "id": 45,
      "agent_code": "AGT001",
      "referral_link": "https://easypool.app/ref/AGT001",
      "status": "active"
    }
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 📋 Form Submission Flow

### 2. Life Insurance Lead Form

**Flutter Model (Dart):**
```dart
class LifeInsuranceLeadForm {
  final String fullName;
  final DateTime dateOfBirth;
  final String email;
  final String phone;
  final int coverageAmount;
  final String? medicalHistory;
  final List<String> beneficiaries;

  Map<String, dynamic> toJson() => {
    'full_name': fullName,
    'date_of_birth': dateOfBirth.toIso8601String(),
    'email': email,
    'phone': phone,
    'coverage_amount': coverageAmount,
    'medical_history': medicalHistory,
    'beneficiaries': beneficiaries,
  };
}
```

**Flutter sends to Backend:**
```json
POST /api/leads/life-insurance/
Headers:
  Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
  Content-Type: application/json

Body:
{
  "product_id": 15,
  "form_data": {
    "full_name": "Rahul Kumar",
    "date_of_birth": "1990-05-15",
    "email": "rahul@example.com",
    "phone": "+919876543210",
    "coverage_amount": 1000000,
    "medical_history": "No pre-existing conditions",
    "beneficiaries": ["Priya Kumar", "Amit Kumar"]
  },
  "source": "mobile_app",
  "referral_code": "AGT001"
}
```

**Django receives and processes:**
```python
# Django View
class LifeInsuranceLeadView(APIView):
    def post(self, request):
        # Django automatically parses JSON to Python dict
        data = request.data

        # Access nested data
        form_data = data.get('form_data', {})
        full_name = form_data.get('full_name')  # "Rahul Kumar"
        dob = form_data.get('date_of_birth')    # "1990-05-15"
        coverage = form_data.get('coverage_amount')  # 1000000

        # Validate using serializer
        serializer = LifeInsuranceLeadSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
```

**Django Serializer:**
```python
class LifeInsuranceLeadSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    form_data = serializers.JSONField()  # Accepts any valid JSON
    source = serializers.CharField(max_length=50)
    referral_code = serializers.CharField(max_length=20)

    def validate_form_data(self, value):
        # Validate nested form_data
        required_fields = ['full_name', 'date_of_birth', 'email', 'phone', 'coverage_amount']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")

        # Validate age
        dob = datetime.fromisoformat(value['date_of_birth'])
        age = (datetime.now() - dob).days / 365
        if age < 18 or age > 65:
            raise serializers.ValidationError("Age must be between 18 and 65")

        return value
```

**Django responds:**
```json
{
  "success": true,
  "lead_id": 789,
  "reference_number": "LI-2025-789",
  "status": "submitted",
  "message": "Lead submitted successfully",
  "created_at": "2025-11-10T12:30:45.123456Z"
}
```

---

## 📄 Form with File Uploads

### 3. Health Insurance with Documents

**Flutter sends (Multipart Form Data):**
```
POST /api/leads/health-insurance/
Headers:
  Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
  Content-Type: multipart/form-data

Form Data:
  product_id: 20
  form_data: {"full_name": "Priya Sharma", "age": 28, "city": "Mumbai"}
  source: mobile_app
  referral_code: AGT001
  documents[0]: (binary file - photo_id.jpg)
  documents[1]: (binary file - medical_report.pdf)
```

**Django receives:**
```python
class HealthInsuranceLeadView(APIView):
    parser_classes = [MultiPartParser, JSONParser]

    def post(self, request):
        # Get form fields
        product_id = request.data.get('product_id')
        form_data = json.loads(request.data.get('form_data', '{}'))

        # Get uploaded files
        files = request.FILES.getlist('documents')

        # Process each file
        for file in files:
            # file.name - filename
            # file.read() - binary content
            # file.size - file size in bytes
            # file.content_type - MIME type
            pass
```

**Django responds:**
```json
{
  "success": true,
  "lead_id": 790,
  "reference_number": "HI-2025-790",
  "uploaded_documents": [
    {
      "id": 101,
      "filename": "photo_id.jpg",
      "size": 245632,
      "url": "https://cdn.easypool.app/documents/photo_id_abc123.jpg"
    },
    {
      "id": 102,
      "filename": "medical_report.pdf",
      "size": 1024000,
      "url": "https://cdn.easypool.app/documents/medical_report_xyz789.pdf"
    }
  ]
}
```

---

## 📊 List/Query Data

### 4. Get Agent's Leads

**Flutter sends:**
```
GET /api/leads/?status=active&page=1&page_size=20
Headers:
  Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Django responds:**
```json
{
  "count": 45,
  "next": "/api/leads/?status=active&page=2&page_size=20",
  "previous": null,
  "results": [
    {
      "id": 789,
      "reference_number": "LI-2025-789",
      "product": {
        "id": 15,
        "name": "Term Life Insurance",
        "category": "life_insurance"
      },
      "customer_name": "Rahul Kumar",
      "status": "submitted",
      "created_at": "2025-11-10T12:30:45Z",
      "updated_at": "2025-11-10T12:30:45Z"
    },
    {
      "id": 788,
      "reference_number": "HI-2025-788",
      "product": {
        "id": 20,
        "name": "Family Health Plan",
        "category": "health_insurance"
      },
      "customer_name": "Priya Sharma",
      "status": "in_progress",
      "created_at": "2025-11-09T15:20:30Z",
      "updated_at": "2025-11-10T10:15:22Z"
    }
  ]
}
```

---

## 🏷️ Get Products and Form Templates

### 5. Get Available Products

**Flutter sends:**
```
GET /api/products/?category=life_insurance
Headers:
  Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Django responds:**
```json
{
  "results": [
    {
      "id": 15,
      "name": "Term Life Insurance",
      "category": "life_insurance",
      "provider": "HDFC Life",
      "commission_rate": 5.5,
      "active": true,
      "form_fields": {
        "fields": [
          {
            "name": "full_name",
            "type": "text",
            "label": "Full Name",
            "required": true,
            "validation": {
              "min_length": 3,
              "max_length": 100
            }
          },
          {
            "name": "date_of_birth",
            "type": "date",
            "label": "Date of Birth",
            "required": true,
            "validation": {
              "min_age": 18,
              "max_age": 65
            }
          },
          {
            "name": "coverage_amount",
            "type": "select",
            "label": "Coverage Amount",
            "required": true,
            "options": [
              {"value": 500000, "label": "₹5 Lakh"},
              {"value": 1000000, "label": "₹10 Lakh"},
              {"value": 2000000, "label": "₹20 Lakh"}
            ]
          }
        ]
      }
    }
  ]
}
```

---

## ⚠️ Error Responses

### Validation Error
```json
{
  "success": false,
  "error": "validation_error",
  "message": "Invalid form data",
  "errors": {
    "form_data.date_of_birth": ["Age must be between 18 and 65"],
    "form_data.phone": ["Enter a valid phone number"]
  }
}
```

### Authentication Error
```json
{
  "success": false,
  "error": "authentication_failed",
  "message": "Invalid or expired token"
}
```

### Not Found Error
```json
{
  "success": false,
  "error": "not_found",
  "message": "Product not found"
}
```

---

## 🔑 Key Points

1. **Always JSON**: Flutter sends JSON, Django receives Python dict
2. **Date Format**: ISO 8601 (`2025-11-10T12:30:45Z`)
3. **Numbers**: Plain integers/floats (no quotes)
4. **Booleans**: `true`/`false` (lowercase)
5. **Null**: `null` (not `None`)
6. **Arrays**: `[]` (lists in Python)
7. **Objects**: `{}` (dicts in Python)
8. **Files**: Use `multipart/form-data` with base64 or binary
9. **Authentication**: JWT token in `Authorization: Bearer <token>` header
10. **Form Data**: Nested in `form_data` field as flexible JSON

---

## 📦 Storage in Django

```python
# Django Model
class Lead(models.Model):
    reference_number = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT)

    # Store entire form submission as JSON
    form_data = models.JSONField()  # PostgreSQL JSONField

    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    # Can query JSON fields in PostgreSQL
    # Lead.objects.filter(form_data__full_name__icontains='Rahul')
```

This allows flexible storage without schema changes!
