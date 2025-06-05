from django.core.management.base import BaseCommand
from django.db import transaction
from admin_app.models import FloatingHolidayPolicy, Country  # Replace 'your_app' with your actual app name


class Command(BaseCommand):
    help = 'Populate FloatingHolidayPolicy model with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before adding new data',
        )

    def handle(self, *args, **options):
        # Data to be inserted
        floating_holiday_policies_data = [
            {'year': 2025, 'allowed_floating_holidays': 2, 'country_id': 1},
            {'year': 2025, 'allowed_floating_holidays': 0, 'country_id': 2},
        ]

        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing FloatingHolidayPolicy data...')
            )
            FloatingHolidayPolicy.objects.all().delete()

        # Check if countries exist
        missing_countries = []
        for data in floating_holiday_policies_data:
            try:
                Country.objects.get(id=data['country_id'])
            except Country.DoesNotExist:
                missing_countries.append(data['country_id'])

        if missing_countries:
            self.stdout.write(
                self.style.ERROR(
                    f'Required countries not found (IDs: {", ".join(map(str, set(missing_countries)))}). '
                    'Please run populate_countries command first.'
                )
            )
            return

        with transaction.atomic():
            created_count = 0
            updated_count = 0
            error_count = 0

            for data in floating_holiday_policies_data:
                try:
                    country = Country.objects.get(id=data['country_id'])
                    
                    policy, created = FloatingHolidayPolicy.objects.get_or_create(
                        year=data['year'],
                        country=country,
                        defaults={'allowed_floating_holidays': data['allowed_floating_holidays']}
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created FloatingHolidayPolicy: {policy.year} - '
                                f'{policy.allowed_floating_holidays} floating holidays for {policy.country.country_name}'
                            )
                        )
                    else:
                        # Update the allowed_floating_holidays if it's different
                        if policy.allowed_floating_holidays != data['allowed_floating_holidays']:
                            policy.allowed_floating_holidays = data['allowed_floating_holidays']
                            policy.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Updated FloatingHolidayPolicy: {policy.year} - '
                                    f'{policy.allowed_floating_holidays} floating holidays for {policy.country.country_name}'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.HTTP_INFO(
                                    f'FloatingHolidayPolicy already exists: {policy.year} - '
                                    f'{policy.allowed_floating_holidays} floating holidays for {policy.country.country_name}'
                                )
                            )

                except Country.DoesNotExist:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Country with ID {data["country_id"]} not found for year {data["year"]}'
                        )
                    )
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error creating FloatingHolidayPolicy for year {data["year"]}: {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} created, {updated_count} updated, {error_count} errors'
            )
        )