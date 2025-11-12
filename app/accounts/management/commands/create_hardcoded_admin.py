"""
Create hardcoded bootstrap admin - runs automatically on container startup
Google Cloud best practice: Bootstrap admin for initial access
Admin should change password after first login via Django admin
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError

User = get_user_model()

# HARDCODED CREDENTIALS - Admin should change password after first login
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@bridge.internal"
ADMIN_PASSWORD = "admin"  # Change via Django admin after first login


class Command(BaseCommand):
    help = "Create/update hardcoded bootstrap admin (idempotent, safe to run multiple times)"

    def handle(self, *args, **options):
        # Check if database is ready and migrations are applied
        try:
            from django.db.migrations.executor import MigrationExecutor

            executor = MigrationExecutor(connection)

            # Check if there are any unapplied migrations
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if plan:
                self.stdout.write("[SKIP] Migrations not fully applied. Run migrate first.")
                return

            # Verify User model is accessible
            User.objects.exists()
        except (OperationalError, Exception) as e:
            self.stdout.write(f"[SKIP] Database not ready: {e}")
            return

        try:
            # Idempotent: Create or update admin user
            user, created = User.objects.update_or_create(
                username=ADMIN_USERNAME,
                defaults={
                    "email": ADMIN_EMAIL,
                    "is_staff": True,
                    "is_superuser": True,
                    "is_active": True,
                },
            )
            user.set_password(ADMIN_PASSWORD)
            user.save()

            action = "Created" if created else "Updated"
            self.stdout.write(f"✅ [{action}] Bootstrap admin: {ADMIN_USERNAME}")
            self.stdout.write(f"   Username: {ADMIN_USERNAME}")
            self.stdout.write(f"   Password: {ADMIN_PASSWORD}")
            self.stdout.write("   🔐 Change password after first login!")

        except Exception as e:
            self.stdout.write(f"[ERROR] Failed to create bootstrap admin: {e}")
