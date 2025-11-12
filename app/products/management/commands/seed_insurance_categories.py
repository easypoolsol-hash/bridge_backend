"""
Management command to seed initial insurance categories
Run: python manage.py seed_insurance_categories
"""

from django.core.management.base import BaseCommand

from products.models import MainCategory, SubCategory


class Command(BaseCommand):
    help = "Seed initial insurance categories for agent lead collection"

    def handle(self, *args, **options):
        self.stdout.write("Seeding insurance categories...")

        # Create Main Category: Insurance
        insurance, created = MainCategory.objects.get_or_create(
            slug="insurance",
            defaults={
                "name": "Insurance",
                "icon": "security",
                "description": "Insurance products - Health, Life, Motor, and more",
                "active": True,
                "display_order": 1,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Created main category: {insurance.name}"))
        else:
            self.stdout.write(f"  Main category already exists: {insurance.name}")

        # Insurance Sub-Categories
        sub_categories = [
            {
                "name": "Health Insurance",
                "slug": "health-insurance",
                "icon": "health_and_safety",
                "description": "Medical and health coverage",
                "display_order": 1,
            },
            {
                "name": "Life Insurance",
                "slug": "life-insurance",
                "icon": "favorite",
                "description": "Life protection and term plans",
                "display_order": 2,
            },
            {
                "name": "Car Insurance",
                "slug": "car-insurance",
                "icon": "directions_car",
                "description": "Four-wheeler insurance coverage",
                "display_order": 3,
            },
            {
                "name": "Motor/Bike Insurance",
                "slug": "motor-bike-insurance",
                "icon": "two_wheeler",
                "description": "Two-wheeler insurance coverage",
                "display_order": 4,
            },
            {
                "name": "Vehicle Insurance",
                "slug": "vehicle-insurance",
                "icon": "local_shipping",
                "description": "Commercial vehicle insurance",
                "display_order": 5,
            },
            {
                "name": "Corporate Insurance",
                "slug": "corporate-insurance",
                "icon": "business",
                "description": "Business and corporate insurance",
                "display_order": 6,
            },
        ]

        for sub_cat_data in sub_categories:
            sub_cat, created = SubCategory.objects.get_or_create(
                main_category=insurance,
                slug=sub_cat_data["slug"],
                defaults={
                    "name": sub_cat_data["name"],
                    "icon": sub_cat_data["icon"],
                    "description": sub_cat_data["description"],
                    "active": True,
                    "display_order": sub_cat_data["display_order"],
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"  ✓ Created: {sub_cat.name}"))
            else:
                self.stdout.write(f"    Sub-category already exists: {sub_cat.name}")

        self.stdout.write(self.style.SUCCESS("\n✅ Insurance categories seeded successfully!"))
        self.stdout.write("\nNext steps:")
        self.stdout.write("  - Agents can now browse categories via API")
        self.stdout.write("  - Create leads by selecting insurance type")
        self.stdout.write("  - Products can be added later from Django admin")
