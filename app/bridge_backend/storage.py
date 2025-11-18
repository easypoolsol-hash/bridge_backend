"""
Google Cloud Storage Backend
Following Fortune 500 best practices for file storage
"""

import os
from django.core.files.storage import Storage
from google.cloud import storage
from google.oauth2 import service_account
import json


class GoogleCloudStorage(Storage):
    """
    Custom storage backend for Google Cloud Storage
    Used for storing lead PDFs and documents
    """

    def __init__(self):
        # Get GCS configuration from environment
        self.bucket_name = os.environ.get('GCS_BUCKET_NAME', 'bridge-lead-pdfs')
        self.project_id = os.environ.get('GCS_PROJECT_ID', 'bridge-477812')
        credentials_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')

        if credentials_json:
            # Use service account from environment variable
            credentials_dict = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict
            )
            self.client = storage.Client(
                credentials=credentials,
                project=self.project_id
            )
        else:
            # Use default credentials (Cloud Run service account)
            self.client = storage.Client(project=self.project_id)

        self.bucket = self.client.bucket(self.bucket_name)

    def _save(self, name, content):
        """
        Save file to GCS

        Args:
            name: File path/name
            content: File content

        Returns:
            str: Saved file name
        """
        blob = self.bucket.blob(name)

        # Upload file
        blob.upload_from_file(content, rewind=True)

        # Note: Bucket has uniform bucket-level access enabled
        # Objects inherit bucket's public access settings automatically

        return name

    def _open(self, name, mode='rb'):
        """
        Open file from GCS

        Args:
            name: File path/name
            mode: File open mode

        Returns:
            File-like object
        """
        from io import BytesIO

        blob = self.bucket.blob(name)
        content = blob.download_as_bytes()

        return BytesIO(content)

    def exists(self, name):
        """
        Check if file exists in GCS

        Args:
            name: File path/name

        Returns:
            bool: True if file exists
        """
        blob = self.bucket.blob(name)
        return blob.exists()

    def url(self, name):
        """
        Get signed URL for file (secure, time-limited access)

        Uses IAM signBlob API for Cloud Run environments without service account keys.
        Works on Cloud Run with Service Account Token Creator IAM role.

        Args:
            name: File path/name

        Returns:
            str: Signed URL (expires in 1 hour)

        Raises:
            google.api_core.exceptions.PermissionDenied: If service account lacks Token Creator role
        """
        from datetime import timedelta
        from google import auth
        from google.auth.transport import requests

        blob = self.bucket.blob(name)

        # Get default credentials with IAM scope to enable signBlob API
        # This is Google's standard approach for Cloud Run 2025
        credentials, _project_id = auth.default(
            scopes=["https://www.googleapis.com/auth/iam"]
        )

        # Refresh credentials to obtain access token (required for signing)
        auth_request = requests.Request()
        credentials.refresh(auth_request)

        # Generate signed URL using IAM signBlob API
        # Requires both service_account_email and access_token for Cloud Run
        # This is the industry standard pattern for Cloud Run without service account keys
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="GET",
            service_account_email=credentials.service_account_email,
            access_token=credentials.token,
        )

        print(f"[GCS] Generated signed URL for {name} (expires in 1 hour)")
        return signed_url

    def delete(self, name):
        """
        Delete file from GCS

        Args:
            name: File path/name
        """
        blob = self.bucket.blob(name)
        blob.delete()

    def size(self, name):
        """
        Get file size

        Args:
            name: File path/name

        Returns:
            int: File size in bytes
        """
        blob = self.bucket.blob(name)
        blob.reload()
        return blob.size

    def get_available_name(self, name, max_length=None):
        """
        Get available filename (overwrites existing)

        Args:
            name: Desired filename
            max_length: Maximum length

        Returns:
            str: Available filename
        """
        return name


class LocalFileStorage(Storage):
    """
    Fallback to local file storage for development
    """
    from django.core.files.storage import FileSystemStorage

    def __init__(self):
        from django.conf import settings
        self.location = settings.MEDIA_ROOT
        self.base_url = settings.MEDIA_URL
        self._storage = FileSystemStorage(location=self.location, base_url=self.base_url)

    def _save(self, name, content):
        return self._storage.save(name, content)

    def _open(self, name, mode='rb'):
        return self._storage.open(name, mode)

    def exists(self, name):
        return self._storage.exists(name)

    def url(self, name):
        url = self._storage.url(name)
        print(f"[LOCAL] Generating URL for {name}: {url}")
        return url

    def delete(self, name):
        return self._storage.delete(name)

    def size(self, name):
        return self._storage.size(name)

    def get_available_name(self, name, max_length=None):
        return self._storage.get_available_name(name, max_length)
