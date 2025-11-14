"""
Google Cloud Storage Backend
Following Fortune 500 best practices for file storage
"""

import os
from django.core.files.storage import Storage
from django.utils.decoding import force_bytes, force_str
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
        credentials_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')

        if credentials_json:
            # Use service account from environment variable
            credentials_dict = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict
            )
            self.client = storage.Client(credentials=credentials)
        else:
            # Use default credentials (for local development)
            self.client = storage.Client()

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

        # Make publicly accessible (for PDF downloads)
        blob.make_public()

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
        Get public URL for file

        Args:
            name: File path/name

        Returns:
            str: Public URL (full GCS URL)
        """
        # Return full GCS public URL
        # Format: https://storage.googleapis.com/{bucket_name}/{file_path}
        return f"https://storage.googleapis.com/{self.bucket_name}/{name}"

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
        return self._storage.url(name)

    def delete(self, name):
        return self._storage.delete(name)

    def size(self, name):
        return self._storage.size(name)

    def get_available_name(self, name, max_length=None):
        return self._storage.get_available_name(name, max_length)
