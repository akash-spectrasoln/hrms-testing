from django.core.management.base import BaseCommand
from django.db import transaction
from admin_app.models import EmployeeType  # Replace 'your_app' with your actual app name


class Command(BaseCommand):
    help = 'Populate EmployeeType model with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before adding new data',
        )

    def handle(self, *args, **options):
        # Data to be inserted
        employee_types_data = [
            {'code': 'C-', 'name': 'Contractor'},
            {'code': 'I-', 'name': 'Intern'},
            {'code': 'E-', 'name': 'Employee'},
        ]

        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing EmployeeType data...')
            )
            EmployeeType.objects.all().delete()

        with transaction.atomic():
            created_count = 0
            updated_count = 0

            for data in employee_types_data:
                employee_type, created = EmployeeType.objects.get_or_create(
                    code=data['code'],
                    defaults={'name': data['name']}
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created EmployeeType: {employee_type.code} - {employee_type.name}'
                        )
                    )
                else:
                    # Update the name if it's different
                    if employee_type.name != data['name']:
                        employee_type.name = data['name']
                        employee_type.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'Updated EmployeeType: {employee_type.code} - {employee_type.name}'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.HTTP_INFO(
                                f'EmployeeType already exists: {employee_type.code} - {employee_type.name}'
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} created, {updated_count} updated'
            )
        )