from django.core.management.base import BaseCommand
from django.db import transaction
from admin_app.models import Role  # Replace 'your_app' with your actual app name


class Command(BaseCommand):
    help = 'Populate Role model with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before adding new data',
        )

    def handle(self, *args, **options):
        # Data to be inserted
        roles_data = [
            {'role_id': '1', 'role_name': 'Accountant'},
            {'role_id': '2', 'role_name': 'Business Analyst'},
            {'role_id': '3', 'role_name': 'Data Scientist'},
            {'role_id': '4', 'role_name': 'Database Administrator'},
            {'role_id': '5', 'role_name': 'HR Coordinator'},
            {'role_id': '6', 'role_name': 'HR Specialist'},
            {'role_id': '7', 'role_name': 'IT Infra Manager'},
            {'role_id': '8', 'role_name': 'Jr. software Engineer'},
            {'role_id': '9', 'role_name': 'Learning and Development Manager'},
            {'role_id': '10', 'role_name': 'Payroll Coordinator'},
            {'role_id': '11', 'role_name': 'Principal Software Engineer'},
            {'role_id': '12', 'role_name': 'Procurement Manager'},
            {'role_id': '13', 'role_name': 'Project Manager'},
            {'role_id': '14', 'role_name': 'Quality Controller'},
            {'role_id': '15', 'role_name': 'Recruiting Coordinator'},
            {'role_id': '16', 'role_name': 'Software Architect'},
            {'role_id': '17', 'role_name': 'Sr. Software Engineer'},
            {'role_id': '18', 'role_name': 'Technical Project Manager'},
        ]

        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing Role data...')
            )
            Role.objects.all().delete()

        with transaction.atomic():
            created_count = 0
            updated_count = 0

            for data in roles_data:
                try:
                    role, created = Role.objects.get_or_create(
                        role_id=data['role_id'],
                        defaults={'role_name': data['role_name']}
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created Role: {role.role_id} - {role.role_name}'
                            )
                        )
                    else:
                        # Update the role name if it's different
                        if role.role_name != data['role_name']:
                            role.role_name = data['role_name']
                            role.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Updated Role: {role.role_id} - {role.role_name}'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.HTTP_INFO(
                                    f'Role already exists: {role.role_id} - {role.role_name}'
                                )
                            )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error creating role {data["role_id"]}: {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} created, {updated_count} updated'
            )
        )