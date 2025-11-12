"""
Management command to seed form templates
Usage: python manage.py seed_forms
For Google Cloud Job: gcloud run jobs execute seed-forms --region=asia-south1
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from leads.models_forms import FormTemplate
from products.models import Product


class Command(BaseCommand):
    help = 'Seed form templates for different insurance products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing forms before seeding',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing form templates...')
            FormTemplate.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('[OK] Cleared'))

        self.stdout.write('Seeding form templates...')

        # Get products (optional - forms can work without products)
        try:
            life_product = Product.objects.filter(name__icontains='life').first()
            health_product = Product.objects.filter(name__icontains='health').first()
            car_product = Product.objects.filter(name__icontains='car').first()
        except Product.DoesNotExist:
            life_product = health_product = car_product = None

        forms_created = 0

        # ==================== Life Insurance Form ====================
        life_insurance_form, created = FormTemplate.objects.get_or_create(
            title='Life Insurance Application',
            defaults={
                'description': 'Complete this form to apply for life insurance coverage. '
                               'Protect your family\'s financial future.',
                'product': life_product,
                'is_shareable': True,
                'is_active': True,
                'schema': {
                    'fields': [
                        {
                            'name': 'customer_name',
                            'label': 'Full Name',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'Enter your full legal name'
                        },
                        {
                            'name': 'email',
                            'label': 'Email Address',
                            'type': 'email',
                            'required': True,
                            'placeholder': 'your@email.com'
                        },
                        {
                            'name': 'phone',
                            'label': 'Mobile Number',
                            'type': 'phone',
                            'required': True,
                            'placeholder': '10-digit mobile number'
                        },
                        {
                            'name': 'date_of_birth',
                            'label': 'Date of Birth',
                            'type': 'date',
                            'required': True
                        },
                        {
                            'name': 'gender',
                            'label': 'Gender',
                            'type': 'radio',
                            'required': True,
                            'options': [
                                {'value': 'male', 'label': 'Male'},
                                {'value': 'female', 'label': 'Female'},
                                {'value': 'other', 'label': 'Other'}
                            ]
                        },
                        {
                            'name': 'coverage_amount',
                            'label': 'Coverage Amount',
                            'type': 'number',
                            'required': True,
                            'suffix': '₹',
                            'placeholder': 'e.g., 1000000'
                        },
                        {
                            'name': 'policy_term',
                            'label': 'Policy Term (Years)',
                            'type': 'number',
                            'required': True,
                            'placeholder': 'e.g., 20'
                        },
                        {
                            'name': 'nominee_name',
                            'label': 'Nominee Name',
                            'type': 'text',
                            'required': True
                        },
                        {
                            'name': 'nominee_relationship',
                            'label': 'Relationship with Nominee',
                            'type': 'dropdown',
                            'required': True,
                            'options': [
                                {'value': 'spouse', 'label': 'Spouse'},
                                {'value': 'parent', 'label': 'Parent'},
                                {'value': 'child', 'label': 'Child'},
                                {'value': 'sibling', 'label': 'Sibling'},
                                {'value': 'other', 'label': 'Other'}
                            ]
                        },
                        {
                            'name': 'annual_income',
                            'label': 'Annual Income',
                            'type': 'number',
                            'required': True,
                            'suffix': '₹'
                        }
                    ]
                }
            }
        )
        if created:
            forms_created += 1
            self.stdout.write(self.style.SUCCESS(f'[OK] Created: {life_insurance_form.title}'))

        # ==================== Health Insurance Form ====================
        health_insurance_form, created = FormTemplate.objects.get_or_create(
            title='Health Insurance Application',
            defaults={
                'description': 'Get comprehensive health coverage for you and your family. '
                               'Cashless treatment at network hospitals.',
                'product': health_product,
                'is_shareable': True,
                'is_active': True,
                'schema': {
                    'fields': [
                        {
                            'name': 'customer_name',
                            'label': 'Full Name',
                            'type': 'text',
                            'required': True
                        },
                        {
                            'name': 'email',
                            'label': 'Email Address',
                            'type': 'email',
                            'required': True
                        },
                        {
                            'name': 'phone',
                            'label': 'Mobile Number',
                            'type': 'phone',
                            'required': True
                        },
                        {
                            'name': 'age',
                            'label': 'Age',
                            'type': 'number',
                            'required': True
                        },
                        {
                            'name': 'coverage_type',
                            'label': 'Coverage Type',
                            'type': 'radio',
                            'required': True,
                            'options': [
                                {'value': 'individual', 'label': 'Individual'},
                                {'value': 'family_floater', 'label': 'Family Floater'},
                                {'value': 'senior_citizen', 'label': 'Senior Citizen'}
                            ]
                        },
                        {
                            'name': 'sum_insured',
                            'label': 'Sum Insured',
                            'type': 'dropdown',
                            'required': True,
                            'options': [
                                {'value': '300000', 'label': '₹3 Lakh'},
                                {'value': '500000', 'label': '₹5 Lakh'},
                                {'value': '1000000', 'label': '₹10 Lakh'},
                                {'value': '2000000', 'label': '₹20 Lakh'},
                                {'value': '5000000', 'label': '₹50 Lakh'}
                            ]
                        },
                        {
                            'name': 'pre_existing_conditions',
                            'label': 'Any Pre-existing Medical Conditions?',
                            'type': 'textarea',
                            'required': False,
                            'placeholder': 'Please list any existing medical conditions'
                        },
                        {
                            'name': 'number_of_members',
                            'label': 'Number of Family Members to Cover',
                            'type': 'number',
                            'required': True
                        }
                    ]
                }
            }
        )
        if created:
            forms_created += 1
            self.stdout.write(self.style.SUCCESS(f'[OK] Created: {health_insurance_form.title}'))

        # ==================== Car Insurance Form ====================
        car_insurance_form, created = FormTemplate.objects.get_or_create(
            title='Car Insurance Application',
            defaults={
                'description': 'Comprehensive car insurance with cashless claim settlement. '
                               'Get instant quote.',
                'product': car_product,
                'is_shareable': True,
                'is_active': True,
                'schema': {
                    'fields': [
                        {
                            'name': 'customer_name',
                            'label': 'Full Name',
                            'type': 'text',
                            'required': True
                        },
                        {
                            'name': 'email',
                            'label': 'Email Address',
                            'type': 'email',
                            'required': True
                        },
                        {
                            'name': 'phone',
                            'label': 'Mobile Number',
                            'type': 'phone',
                            'required': True
                        },
                        {
                            'name': 'vehicle_number',
                            'label': 'Vehicle Registration Number',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'e.g., MH01AB1234'
                        },
                        {
                            'name': 'vehicle_make',
                            'label': 'Vehicle Make',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'e.g., Maruti, Hyundai, Honda'
                        },
                        {
                            'name': 'vehicle_model',
                            'label': 'Vehicle Model',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'e.g., Swift, i20, City'
                        },
                        {
                            'name': 'manufacturing_year',
                            'label': 'Year of Manufacture',
                            'type': 'number',
                            'required': True,
                            'placeholder': 'e.g., 2020'
                        },
                        {
                            'name': 'insurance_type',
                            'label': 'Insurance Type',
                            'type': 'radio',
                            'required': True,
                            'options': [
                                {'value': 'comprehensive', 'label': 'Comprehensive'},
                                {'value': 'third_party', 'label': 'Third Party Only'}
                            ]
                        },
                        {
                            'name': 'is_new_vehicle',
                            'label': 'Is this a new vehicle (less than 1 year old)?',
                            'type': 'radio',
                            'required': True,
                            'options': [
                                {'value': 'yes', 'label': 'Yes'},
                                {'value': 'no', 'label': 'No'}
                            ]
                        },
                        {
                            'name': 'previous_insurance_expiry',
                            'label': 'Previous Insurance Expiry Date',
                            'type': 'date',
                            'required': False
                        }
                    ]
                }
            }
        )
        if created:
            forms_created += 1
            self.stdout.write(self.style.SUCCESS(f'[OK] Created: {car_insurance_form.title}'))

        # Summary
        total_forms = FormTemplate.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\n[SUCCESS] Seeding complete! {forms_created} new forms created. Total forms: {total_forms}'
        ))

        # Display share URLs
        self.stdout.write('\n[SHARE URLS]')
        for form in FormTemplate.objects.filter(is_shareable=True):
            share_url = f"http://localhost:8080{form.share_url}" if form.share_url else "N/A"
            self.stdout.write(f'  - {form.title}: {share_url}')
