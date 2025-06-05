from django.core.management.base import BaseCommand
from django.db import transaction
from admin_app.models import HolidayResetPeriod, Country  # Replace 'your_app' with your actual app name


class Command(BaseCommand):
    help = 'Populate HolidayResetPeriod model with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before adding new data',
        )

    def handle(self, *args, **options):
        # Data to be inserted - Updated to start from June 1st for both countries
        holiday_reset_periods_data = [
            # India: June 1st to May 31st
            {'start_month': 6, 'start_day': 1, 'end_month': 5, 'end_day': 31, 'country_id': 1},
            # United States: June 1st to May 31st  
            {'start_month': 6, 'start_day': 1, 'end_month': 5, 'end_day': 31, 'country_id': 2},
        ]

        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing HolidayResetPeriod data...')
            )
            HolidayResetPeriod.objects.all().delete()

        # Check if countries exist and get their names for better output
        country_info = {}
        missing_countries = []
        
        for data in holiday_reset_periods_data:
            try:
                country = Country.objects.get(id=data['country_id'])
                country_info[data['country_id']] = country.country_name
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

        # Helper function to format month names
        def get_month_name(month_num):
            months = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April',
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            }
            return months.get(month_num, str(month_num))

        self.stdout.write(
            self.style.HTTP_INFO('Populating holiday reset periods (June 1st to May 31st cycle)...')
        )

        with transaction.atomic():
            created_count = 0
            updated_count = 0
            error_count = 0

            for data in holiday_reset_periods_data:
                try:
                    country = Country.objects.get(id=data['country_id'])
                    country_name = country_info[data['country_id']]
                    
                    # Use OneToOneField relationship - country is unique
                    reset_period, created = HolidayResetPeriod.objects.get_or_create(
                        country=country,
                        defaults={
                            'start_month': data['start_month'],
                            'start_day': data['start_day'],
                            'end_month': data['end_month'],
                            'end_day': data['end_day']
                        }
                    )

                    start_month_name = get_month_name(data['start_month'])
                    end_month_name = get_month_name(data['end_month'])
                    period_description = f"{start_month_name} {data['start_day']} to {end_month_name} {data['end_day']}"

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created: {country_name} - Holiday reset period: {period_description}'
                            )
                        )
                    else:
                        # Update fields if they're different
                        updated = False
                        old_period = f"{get_month_name(reset_period.start_month)} {reset_period.start_day} to {get_month_name(reset_period.end_month)} {reset_period.end_day}"
                        
                        if (reset_period.start_month != data['start_month'] or 
                            reset_period.start_day != data['start_day'] or
                            reset_period.end_month != data['end_month'] or 
                            reset_period.end_day != data['end_day']):
                            
                            reset_period.start_month = data['start_month']
                            reset_period.start_day = data['start_day']
                            reset_period.end_month = data['end_month']
                            reset_period.end_day = data['end_day']
                            reset_period.save()
                            updated = True
                            
                        if updated:
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Updated: {country_name} - Changed from "{old_period}" to "{period_description}"'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.HTTP_INFO(
                                    f'Exists: {country_name} - Holiday reset period: {period_description}'
                                )
                            )

                except Country.DoesNotExist:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Country with ID {data["country_id"]} not found'
                        )
                    )
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error creating HolidayResetPeriod: {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} created, {updated_count} updated, {error_count} errors'
            )
        )

        # Display reset period summary
        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.HTTP_INFO('\nHoliday Reset Period Summary:')
            )
            
            for reset_period in HolidayResetPeriod.objects.all().order_by('country__country_name'):
                start_month_name = get_month_name(reset_period.start_month)
                end_month_name = get_month_name(reset_period.end_month)
                
                self.stdout.write(
                    f'  • {reset_period.country.country_name}: '
                    f'{start_month_name} {reset_period.start_day} to {end_month_name} {reset_period.end_day}'
                )
                
            self.stdout.write(
                self.style.HTTP_INFO(
                    '\nNote: Holiday year runs from June 1st to May 31st for all countries.'
                )
            )