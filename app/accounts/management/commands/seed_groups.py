"""
Seed Django Groups (Roles) and Permissions
Following Google Cloud IAM and Fortune 500 best practices
Groups are version-controlled and immutable via admin panel
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed Groups (Roles) and Permissions - Google Cloud IAM pattern"

    def handle(self, *args, **options):
        """
        Create/update groups with proper permissions.
        Idempotent: Safe to run multiple times.
        """

        # Define groups and their permissions (IAM-style)
        groups_config = {
            "Super Administrator": {
                # Full access to all models
                "accounts": {
                    "user": ["add", "change", "delete", "view"],
                    "agent": ["add", "change", "delete", "view"],
                },
                "leads": {
                    "lead": ["add", "change", "delete", "view"],
                },
                "products": {
                    "product": ["add", "change", "delete", "view"],
                },
            },
            "Admin": {
                # Can manage agents and leads, view products
                "accounts": {
                    "user": ["view", "change"],
                    "agent": ["view", "change"],
                },
                "leads": {
                    "lead": ["add", "view", "change", "delete"],
                },
                "products": {
                    "product": ["view"],
                },
            },
            "Agent": {
                # Can manage own leads, view products
                "leads": {
                    "lead": ["add", "view", "change"],
                },
                "products": {
                    "product": ["view"],
                },
            },
            "New User": {
                # NO permissions - default for Firebase users
                # Admin must manually promote to appropriate role
            },
        }

        self.stdout.write(self.style.MIGRATE_HEADING("🔐 Seeding Groups and Permissions..."))

        for group_name, apps_config in groups_config.items():
            # Create or get group
            group, created = Group.objects.get_or_create(name=group_name)

            # Clear existing permissions (idempotent)
            group.permissions.clear()

            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} group: {group_name}")

            # Add permissions
            permission_count = 0
            for app_label, models_config in apps_config.items():
                for model_name, permission_codes in models_config.items():
                    try:
                        # Get content type for model
                        content_type = ContentType.objects.get(app_label=app_label, model=model_name)

                        for perm_code in permission_codes:
                            # Format: add_user, change_user, delete_user, view_user
                            permission_codename = f"{perm_code}_{model_name}"

                            try:
                                permission = Permission.objects.get(
                                    codename=permission_codename,
                                    content_type=content_type,
                                )
                                group.permissions.add(permission)
                                permission_count += 1

                            except Permission.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"    ⚠️  Permission not found: {permission_codename} "
                                        f"(app: {app_label}, model: {model_name})"
                                    )
                                )

                    except ContentType.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f"    ⚠️  Model not found: {app_label}.{model_name} "
                                f"(run migrations first)"
                            )
                        )

            self.stdout.write(f"    → {permission_count} permissions assigned")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Successfully seeded {len(groups_config)} groups\n"
                f"   Groups are READ-ONLY via admin panel (IAM best practice)\n"
                f"   To modify: Update this file and run 'python manage.py seed_groups'"
            )
        )
