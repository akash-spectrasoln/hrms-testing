from django.core.management.base import BaseCommand
from django.db import transaction
from admin_app.models import Salutation  # Replace 'your_app' with your actual app name


class Command(BaseCommand):
    help = 'Populate Salutation model with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before adding new data',
        )

    def handle(self, *args, **options):
        # Data to be inserted
        salutations_data = [
            {'sal_name': 'Mr.'},
            {'sal_name': 'Mrs.'},
            {'sal_name': 'Miss.'},
        ]

        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing Salutation data...')
            )
            Salutation.objects.all().delete()

        with transaction.atomic():
            created_count = 0
            updated_count = 0

            for data in salutations_data:
                salutation, created = Salutation.objects.get_or_create(
                    sal_name=data['sal_name']
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created Salutation: {salutation.sal_name}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.HTTP_INFO(
                            f'Salutation already exists: {salutation.sal_name}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} created, {updated_count} updated'
            )
        )