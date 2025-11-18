"""
Management command to set up database schemas and permissions for multi-environment isolation.
Run this with: python manage.py setup_database_schemas
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Set up database schemas and permissions for multi-environment isolation"

    def handle(self, *args, **options):
        SQL_COMMANDS = [
            # Create separate schemas for each environment
            "CREATE SCHEMA IF NOT EXISTS dev_schema;",
            "CREATE SCHEMA IF NOT EXISTS staging_schema;",
            "CREATE SCHEMA IF NOT EXISTS production_schema;",
            # Grant usage on schemas
            "GRANT USAGE ON SCHEMA dev_schema TO bridge_dev_user;",
            "GRANT USAGE ON SCHEMA staging_schema TO bridge_staging_user;",
            "GRANT USAGE ON SCHEMA production_schema TO bridge_production_user;",
            # Grant all privileges on all tables in the schemas
            "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dev_schema TO bridge_dev_user;",
            "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging_schema TO bridge_staging_user;",
            "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA production_schema TO bridge_production_user;",
            # Grant all privileges on all sequences in the schemas
            "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA dev_schema TO bridge_dev_user;",
            "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA staging_schema TO bridge_staging_user;",
            "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA production_schema TO bridge_production_user;",
            # Set default privileges for future tables
            "ALTER DEFAULT PRIVILEGES IN SCHEMA dev_schema GRANT ALL ON TABLES TO bridge_dev_user;",
            "ALTER DEFAULT PRIVILEGES IN SCHEMA staging_schema GRANT ALL ON TABLES TO bridge_staging_user;",
            "ALTER DEFAULT PRIVILEGES IN SCHEMA production_schema GRANT ALL ON TABLES TO bridge_production_user;",
            # Set default privileges for future sequences
            "ALTER DEFAULT PRIVILEGES IN SCHEMA dev_schema GRANT ALL ON SEQUENCES TO bridge_dev_user;",
            "ALTER DEFAULT PRIVILEGES IN SCHEMA staging_schema GRANT ALL ON SEQUENCES TO bridge_staging_user;",
            "ALTER DEFAULT PRIVILEGES IN SCHEMA production_schema GRANT ALL ON SEQUENCES TO bridge_production_user;",
            # Set search_path for each user to only their schema
            "ALTER USER bridge_dev_user SET search_path TO dev_schema, public;",
            "ALTER USER bridge_staging_user SET search_path TO staging_schema, public;",
            "ALTER USER bridge_production_user SET search_path TO production_schema, public;",
        ]

        self.stdout.write(self.style.SUCCESS("Setting up database schemas and permissions..."))
        self.stdout.write("=" * 60)

        with connection.cursor() as cursor:
            for i, sql in enumerate(SQL_COMMANDS, 1):
                try:
                    self.stdout.write(f"[{i}/{len(SQL_COMMANDS)}] Executing: {sql[:60]}...")
                    cursor.execute(sql)
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Success"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ Error: {e}"))
                    # Continue with other commands even if one fails

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Database schema setup complete!"))
        self.stdout.write("\nNext steps:")
        self.stdout.write("1. Update DATABASE_URL secrets for each environment")
        self.stdout.write("2. Run migrations on each environment")
