# GCS Storage Setup for PDF Generation

This document explains how to configure Google Cloud Storage for auto-generated lead PDFs.

## ✅ Infrastructure Status

**Terraform Applied:** GCS bucket created successfully!

- **Bucket Name:** `bridge-477812-bridge-lead-pdfs`
- **Public URL:** `https://storage.googleapis.com/bridge-477812-bridge-lead-pdfs`
- **Location:** `asia-south1`
- **Permissions:**
  - Public read access for PDF downloads ✓
  - Backend Cloud Run SA write access ✓

## 📝 Required Environment Variables

Add these to your deployment environment (Cloud Run, GitHub Actions secrets, etc.):

```bash
# Enable GCS storage (set to 'true' for production)
USE_GCS_STORAGE=true

# GCS bucket name for PDF storage
GCS_BUCKET_NAME=bridge-477812-bridge-lead-pdfs

# Google Cloud service account credentials (JSON)
# For Cloud Run: automatically provided via workload identity
# For local dev: Use service account key JSON
GOOGLE_APPLICATION_CREDENTIALS_JSON=<service_account_json>
```

## 🚀 Deployment Methods

### Option 1: Cloud Run (Production) - **RECOMMENDED**

Cloud Run automatically provides credentials via workload identity.

**No additional credentials needed!** Just set:

```bash
USE_GCS_STORAGE=true
GCS_BUCKET_NAME=bridge-477812-bridge-lead-pdfs
```

The `bridge-cloud-run-sa@bridge-477812.iam.gserviceaccount.com` service account already has write permissions.

### Option 2: Local Development

For local development, use local file storage (default):

```bash
# Leave USE_GCS_STORAGE unset or set to 'false'
# PDFs will be stored in: backend_bridge/media/lead_pdfs/
```

Or use GCS locally with a service account key:

```bash
USE_GCS_STORAGE=true
GCS_BUCKET_NAME=bridge-477812-bridge-lead-pdfs
GOOGLE_APPLICATION_CREDENTIALS_JSON='{
  "type": "service_account",
  "project_id": "bridge-477812",
  "private_key_id": "...",
  "private_key": "...",
  ...
}'
```

## 🧪 Testing

### Test PDF Generation Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Create a test lead via admin or API
# PDF will be auto-generated on submission

# 4. Check media folder (local) or GCS bucket (production)
```

### Verify Bucket Access

```bash
# Check if bucket is publicly accessible
curl -I https://storage.googleapis.com/bridge-477812-bridge-lead-pdfs/

# Expected: HTTP 200 OK
```

### Test PDF Upload (Production)

```bash
# Upload a test file to verify permissions
echo "test" > test.txt
gcloud storage cp test.txt gs://bridge-477812-bridge-lead-pdfs/test.txt

# Download via public URL
curl https://storage.googleapis.com/bridge-477812-bridge-lead-pdfs/test.txt

# Clean up
gcloud storage rm gs://bridge-477812-bridge-lead-pdfs/test.txt
```

## 📂 File Organization

PDFs are stored with this structure:

```
bridge-477812-bridge-lead-pdfs/
└── lead_pdfs/
    └── 2025/
        └── 01/
            ├── LI-2025-123_Life_Insurance_20250114.pdf
            ├── HI-2025-456_Health_Insurance_20250114.pdf
            └── ...
```

## 🔒 Security Notes

- **Public Read Access:** PDFs contain lead form data and are publicly accessible via URL
- **Write Access:** Only the backend Cloud Run service account can upload PDFs
- **Compliance:** 7-year retention policy configured (financial records requirement)
- **Versioning:** Enabled for document history

## 🛠️ Troubleshooting

### PDF Generation Fails

**Error:** `No module named 'weasyprint'`

```bash
pip install WeasyPrint==62.3 Pillow==10.2.0
```

**Error:** `Permission denied (GCS)`

Check that `USE_GCS_STORAGE=true` and Cloud Run service account has permissions:

```bash
gcloud storage buckets get-iam-policy gs://bridge-477812-bridge-lead-pdfs
```

Should show `bridge-cloud-run-sa@bridge-477812.iam.gserviceaccount.com` with `roles/storage.objectAdmin`.

### PDF Not Appearing in API

Check backend logs for PDF generation errors:

```bash
# Local
tail -f logs/django.log | grep PDF

# Cloud Run
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~PDF" --limit 50
```

## 📚 Related Documentation

- [PDF Generator Code](app/leads/pdf_generator.py)
- [Storage Backend](app/bridge_backend/storage.py)
- [Terraform Storage Module](../bridge_backend_infra/terragrunt/modules/storage/)
- [Django Settings](app/bridge_backend/settings/base.py#L96-L107)

## ✅ Production Checklist

- [x] Terraform applied - GCS bucket created
- [x] IAM permissions configured
- [x] Dependencies added to requirements.txt and pyproject.toml
- [ ] Environment variables set in Cloud Run
- [ ] Test PDF generation on production
- [ ] Verify PDF download links work in frontend

---

**Infrastructure deployed:** 2025-01-14
**Bucket URL:** https://storage.googleapis.com/bridge-477812-bridge-lead-pdfs
