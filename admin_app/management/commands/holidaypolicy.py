from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import datetime
from admin_app.models import HolidayPolicy, Country  # Replace 'your_app' with your actual app name


class Command(BaseCommand):
    help = 'Populate HolidayPolicy model with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before adding new data',
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Specify a particular year to populate (default: uses data as defined)',
        )
        parser.add_argument(
            '--current-year',
            action='store_true',
            help='Use current year instead of 2025',
        )

    def handle(self, *args, **options):
        # Determine the year to use
        if options['current_year']:
            target_year = datetime.now().year
        elif options['year']:
            target_year = options['year']
        else:
            target_year = 2025  # Default from your data

        # Data to be inserted
        holiday_policies_data = [
            # India policies (country_id = 1)
            {'year': target_year, 'ordinary_holidays_count': 15, 'min_years_experience': 0, 'extra_holidays': 0, 'country_id': 1},
            {'year': target_year, 'ordinary_holidays_count': 15, 'min_years_experience': 6, 'extra_holidays': 2, 'country_id': 1},
            {'year': target_year, 'ordinary_holidays_count': 15, 'min_years_experience': 11, 'extra_holidays': 4, 'country_id': 1},
            # United States policies (country_id = 2)
            {'year': target_year, 'ordinary_holidays_count': 10, 'min_years_experience': 0, 'extra_holidays': 0, 'country_id': 2},
            {'year': target_year, 'ordinary_holidays_count': 10, 'min_years_experience': 6, 'extra_holidays': 2, 'country_id': 2},
        ]

        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing HolidayPolicy data...')
            )
            HolidayPolicy.objects.all().delete()

        # Check if countries exist and get their names for better output
        country_info = {}
        missing_countries = []
        
        for data in holiday_policies_data:
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

        self.stdout.write(
            self.style.HTTP_INFO(f'Populating holiday policies for year: {target_year}')
        )

        with transaction.atomic():
            created_count = 0
            updated_count = 0
            error_count = 0

            for data in holiday_policies_data:
                try:
                    country = Country.objects.get(id=data['country_id'])
                    country_name = country_info[data['country_id']]
                    
                    # Use unique combination of year, country, and min_years_experience
                    policy, created = HolidayPolicy.objects.get_or_create(
                        year=data['year'],
                        country=country,
                        min_years_experience=data['min_years_experience'],
                        defaults={
                            'ordinary_holidays_count': data['ordinary_holidays_count'],
                            'extra_holidays': data['extra_holidays']
                        }
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created: {country_name} {policy.year} - '
                                f'{policy.ordinary_holidays_count} ordinary holidays, '
                                f'{policy.min_years_experience}+ years = +{policy.extra_holidays} extra'
                            )
                        )
                    else:
                        # Update fields if they're different
                        updated = False
                        old_ordinary = policy.ordinary_holidays_count
                        old_extra = policy.extra_holidays
                        
                        if policy.ordinary_holidays_count != data['ordinary_holidays_count']:
                            policy.ordinary_holidays_count = data['ordinary_holidays_count']
                            updated = True
                            
                        if policy.extra_holidays != data['extra_holidays']:
                            policy.extra_holidays = data['extra_holidays']
                            updated = True
                            
                        if updated:
                            policy.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Updated: {country_name} {policy.year} - '
                                    f'ordinary: {old_ordinary}→{policy.ordinary_holidays_count}, '
                                    f'extra ({policy.min_years_experience}+ yrs): {old_extra}→{policy.extra_holidays}'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.HTTP_INFO(
                                    f'Exists: {country_name} {policy.year} - '
                                    f'{policy.ordinary_holidays_count} ordinary, '
                                    f'{policy.min_years_experience}+ years = +{policy.extra_holidays} extra'
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
                            f'Error creating HolidayPolicy: {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary for year {target_year}: {created_count} created, '
                f'{updated_count} updated, {error_count} errors'
            )
        )

        # Display policy summary by country
        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.HTTP_INFO(f'\nHoliday Policy Summary for {target_year}:')
            )
            
            for country_id in sorted(set(data['country_id'] for data in holiday_policies_data)):
                if country_id in country_info:
                    country_name = country_info[country_id]
                    policies = HolidayPolicy.objects.filter(
                        year=target_year, 
                        country_id=country_id
                    ).order_by('min_years_experience')
                    
                    self.stdout.write(f'\n  {country_name}:')
                    for policy in policies:
                        if policy.min_years_experience == 0:
                            self.stdout.write(
                                f'    • Base: {policy.ordinary_holidays_count} holidays'
                            )
                        else:
                            total_holidays = policy.ordinary_holidays_count + policy.extra_holidays
                            self.stdout.write(
                                f'    • {policy.min_years_experience}+ years: {policy.ordinary_holidays_count} + {policy.extra_holidays} = {total_holidays} holidays'
                            )