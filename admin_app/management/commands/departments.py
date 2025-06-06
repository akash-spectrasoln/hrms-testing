from django.core.management.base import BaseCommand
from django.db import transaction
from admin_app.models import Department  # Replace 'your_app' with your actual app name


class Command(BaseCommand):
    help = 'Populate Department model with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before adding new data',
        )

    def handle(self, *args, **options):
        # Data to be inserted
        departments_data = [
            {'dep_name': 'Software Development'},
            {'dep_name': 'QA Engineer'},
            {'dep_name': 'HR'},
            {'dep_name': 'SCM'},
        ]

        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing Department data...')
            )
            Department.objects.all().delete()

        with transaction.atomic():
            created_count = 0
            updated_count = 0

            for data in departments_data:
                department, created = Department.objects.get_or_create(
                    dep_name=data['dep_name']
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created Department: {department.dep_name}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.HTTP_INFO(
                            f'Department already exists: {department.dep_name}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} created, {updated_count} updated'
            )
        )