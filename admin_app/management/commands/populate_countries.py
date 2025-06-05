from django.core.management.base import BaseCommand
from django.db import transaction
from admin_app.models import Country  # Replace 'your_app' with your actual app name


class Command(BaseCommand):
    help = 'Populate Country model with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before adding new data',
        )

    def handle(self, *args, **options):
        # Data to be inserted
        countries_data = [
            {'country_name': 'India', 'code': 'IN'},
            {'country_name': 'United States', 'code': 'US'},
        ]

        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing Country data...')
            )
            Country.objects.all().delete()

        with transaction.atomic():
            created_count = 0
            updated_count = 0

            for data in countries_data:
                country, created = Country.objects.get_or_create(
                    country_name=data['country_name'],
                    defaults={'code': data['code']}
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created Country: {country.country_name} - {country.code}'
                        )
                    )
                else:
                    # Update the code if it's different
                    if country.code != data['code']:
                        country.code = data['code']
                        country.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'Updated Country: {country.country_name} - {country.code}'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.HTTP_INFO(
                                f'Country already exists: {country.country_name} - {country.code}'
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} created, {updated_count} updated'
            )
        )