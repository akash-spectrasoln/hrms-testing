from django.core.management.base import BaseCommand
from django.db import transaction
from admin_app.models import  Country  # Replace 'your_app' with your actual app name
from admin_app.models import state as State

class Command(BaseCommand):
    help = 'Populate State model with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before adding new data',
        )

    def handle(self, *args, **options):
        # Data to be inserted
        states_data = [
            # Indian States (country_id = 1)
            {'name': 'Andhra Pradesh', 'country_id': 1, 'code': 'AP'},
            {'name': 'Arunachal Pradesh', 'country_id': 1, 'code': 'AR'},
            {'name': 'Assam', 'country_id': 1, 'code': 'AS'},
            {'name': 'Bihar', 'country_id': 1, 'code': 'BR'},
            {'name': 'Chhattisgarh', 'country_id': 1, 'code': 'CG'},
            {'name': 'Goa', 'country_id': 1, 'code': 'GA'},
            {'name': 'Gujarat', 'country_id': 1, 'code': 'GJ'},
            {'name': 'Haryana', 'country_id': 1, 'code': 'HR'},
            {'name': 'Himachal Pradesh', 'country_id': 1, 'code': 'HP'},
            {'name': 'Jharkhand', 'country_id': 1, 'code': 'JH'},
            {'name': 'Karnataka', 'country_id': 1, 'code': 'KA'},
            {'name': 'Kerala', 'country_id': 1, 'code': 'KL'},
            {'name': 'Madhya Pradesh', 'country_id': 1, 'code': 'MP'},
            {'name': 'Maharashtra', 'country_id': 1, 'code': 'MH'},
            {'name': 'Manipur', 'country_id': 1, 'code': 'MN'},
            {'name': 'Meghalaya', 'country_id': 1, 'code': 'ML'},
            {'name': 'Mizoram', 'country_id': 1, 'code': 'MZ'},
            {'name': 'Nagaland', 'country_id': 1, 'code': 'NL'},
            {'name': 'Odisha', 'country_id': 1, 'code': 'OD'},
            {'name': 'Punjab', 'country_id': 1, 'code': 'PB'},
            {'name': 'Rajasthan', 'country_id': 1, 'code': 'RJ'},
            {'name': 'Sikkim', 'country_id': 1, 'code': 'SK'},
            {'name': 'Tamil Nadu', 'country_id': 1, 'code': 'TN'},
            {'name': 'Telangana', 'country_id': 1, 'code': 'TS'},
            {'name': 'Tripura', 'country_id': 1, 'code': 'TR'},
            {'name': 'Uttar Pradesh', 'country_id': 1, 'code': 'UP'},
            {'name': 'Uttarakhand', 'country_id': 1, 'code': 'UK'},
            {'name': 'West Bengal', 'country_id': 1, 'code': 'WB'},
            {'name': 'Andaman and Nicobar Islands', 'country_id': 1, 'code': 'AN'},
            {'name': 'Chandigarh', 'country_id': 1, 'code': 'CH'},
            {'name': 'Dadra and Nagar Haveli', 'country_id': 1, 'code': 'DN'},
            {'name': 'Delhi', 'country_id': 1, 'code': 'DL'},
            {'name': 'Jammu and Kashmir', 'country_id': 1, 'code': 'JK'},
            {'name': 'Ladakh', 'country_id': 1, 'code': 'LA'},
            {'name': 'Lakshadweep', 'country_id': 1, 'code': 'LD'},
            {'name': 'Puducherry', 'country_id': 1, 'code': 'PY'},
            
            # US States (country_id = 2)
            {'name': 'Alabama', 'country_id': 2, 'code': 'AL'},
            {'name': 'Alaska', 'country_id': 2, 'code': 'AK'},
            {'name': 'Arizona', 'country_id': 2, 'code': 'AZ'},
            {'name': 'Arkansas', 'country_id': 2, 'code': 'AR'},
            {'name': 'California', 'country_id': 2, 'code': 'CA'},
            {'name': 'Colorado', 'country_id': 2, 'code': 'CO'},
            {'name': 'Connecticut', 'country_id': 2, 'code': 'CT'},
            {'name': 'Delaware', 'country_id': 2, 'code': 'DE'},
            {'name': 'Florida', 'country_id': 2, 'code': 'FL'},
            {'name': 'Georgia', 'country_id': 2, 'code': 'GA'},
            {'name': 'Hawaii', 'country_id': 2, 'code': 'HI'},
            {'name': 'Idaho', 'country_id': 2, 'code': 'ID'},
            {'name': 'Illinois', 'country_id': 2, 'code': 'IL'},
            {'name': 'Indiana', 'country_id': 2, 'code': 'IN'},
            {'name': 'Iowa', 'country_id': 2, 'code': 'IA'},
            {'name': 'Kansas', 'country_id': 2, 'code': 'KS'},
            {'name': 'Kentucky', 'country_id': 2, 'code': 'KY'},
            {'name': 'Louisiana', 'country_id': 2, 'code': 'LA'},
            {'name': 'Maine', 'country_id': 2, 'code': 'ME'},
            {'name': 'Maryland', 'country_id': 2, 'code': 'MD'},
            {'name': 'Massachusetts', 'country_id': 2, 'code': 'MA'},
            {'name': 'Michigan', 'country_id': 2, 'code': 'MI'},
            {'name': 'Minnesota', 'country_id': 2, 'code': 'MN'},
            {'name': 'Mississippi', 'country_id': 2, 'code': 'MS'},
            {'name': 'Missouri', 'country_id': 2, 'code': 'MO'},
            {'name': 'Montana', 'country_id': 2, 'code': 'MT'},
            {'name': 'Nebraska', 'country_id': 2, 'code': 'NE'},
            {'name': 'Nevada', 'country_id': 2, 'code': 'NV'},
            {'name': 'New Hampshire', 'country_id': 2, 'code': 'NH'},
            {'name': 'New Jersey', 'country_id': 2, 'code': 'NJ'},
            {'name': 'New Mexico', 'country_id': 2, 'code': 'NM'},
            {'name': 'New York', 'country_id': 2, 'code': 'NY'},
            {'name': 'North Carolina', 'country_id': 2, 'code': 'NC'},
            {'name': 'North Dakota', 'country_id': 2, 'code': 'ND'},
            {'name': 'Ohio', 'country_id': 2, 'code': 'OH'},
            {'name': 'Oklahoma', 'country_id': 2, 'code': 'OK'},
            {'name': 'Oregon', 'country_id': 2, 'code': 'OR'},
            {'name': 'Pennsylvania', 'country_id': 2, 'code': 'PA'},
            {'name': 'Rhode Island', 'country_id': 2, 'code': 'RI'},
            {'name': 'South Carolina', 'country_id': 2, 'code': 'SC'},
            {'name': 'South Dakota', 'country_id': 2, 'code': 'SD'},
            {'name': 'Tennessee', 'country_id': 2, 'code': 'TN'},
            {'name': 'Texas', 'country_id': 2, 'code': 'TX'},
            {'name': 'Utah', 'country_id': 2, 'code': 'UT'},
            {'name': 'Vermont', 'country_id': 2, 'code': 'VT'},
            {'name': 'Virginia', 'country_id': 2, 'code': 'VA'},
            {'name': 'Washington', 'country_id': 2, 'code': 'WA'},
            {'name': 'West Virginia', 'country_id': 2, 'code': 'WV'},
            {'name': 'Wisconsin', 'country_id': 2, 'code': 'WI'},
            {'name': 'Wyoming', 'country_id': 2, 'code': 'WY'},
        ]

        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing State data...')
            )
            State.objects.all().delete()

        # Check if countries exist
        try:
            india = Country.objects.get(id=1)
            usa = Country.objects.get(id=2)
        except Country.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    'Required countries not found. Please run populate_countries command first.'
                )
            )
            return

        with transaction.atomic():
            created_count = 0
            updated_count = 0
            error_count = 0

            for data in states_data:
                try:
                    country = Country.objects.get(id=data['country_id'])
                    
                    state, created = State.objects.get_or_create(
                        name=data['name'],
                        country=country,
                        defaults={'code': data['code']}
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created State: {state.name} ({state.code}) - {state.country.country_name}'
                            )
                        )
                    else:
                        # Update the code if it's different
                        if state.code != data['code']:
                            state.code = data['code']
                            state.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Updated State: {state.name} ({state.code}) - {state.country.country_name}'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.HTTP_INFO(
                                    f'State already exists: {state.name} ({state.code}) - {state.country.country_name}'
                                )
                            )

                except Country.DoesNotExist:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Country with ID {data["country_id"]} not found for state {data["name"]}'
                        )
                    )
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error creating state {data["name"]}: {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} created, {updated_count} updated, {error_count} errors'
            )
        )