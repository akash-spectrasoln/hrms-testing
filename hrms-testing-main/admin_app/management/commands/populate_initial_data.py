from django.core.management.base import BaseCommand
from datetime import date
from admin_app.models import Role, Salutation, Department, Country, state, Holiday, FloatingHoliday

class Command(BaseCommand):
    help = "Populate initial data for roles, salutations, departments, states, and holidays"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting data population...")

        # Insert roles
        roles = ["Contractor", "Employee", "Intern"]
        for role in roles:
            Role.objects.get_or_create(role_name=role)
            self.stdout.write(f"Inserted role: {role}")

        # Insert salutations
        salutations = ["Mr.", "Mrs."]
        for salutation in salutations:
            Salutation.objects.get_or_create(sal_name=salutation)
            self.stdout.write(f"Inserted salutation: {salutation}")

        # Insert departments
        departments = ["Software Development", "QA Engineer", "HR", "IT Support"]
        for department in departments:
            Department.objects.get_or_create(dep_name=department)
            self.stdout.write(f"Inserted department: {department}")

        # Insert country and states
        country, created = Country.objects.get_or_create(country_name="India")
        self.stdout.write(f"{'Created' if created else 'Already exists'} country: India")

        states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
            "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
            "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
            "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
            "Uttar Pradesh", "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands",
            "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
            "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
        ]

        for state_name in states:
            state, created = state.objects.get_or_create(name=state_name, country=country)
            self.stdout.write(f"{'Created' if created else 'Already exists'} state: {state_name}")

        # Insert holidays
        holidays = [
            {"date": date(2025, 1, 1), "name": "New Year", "day": "Wednesday"},
            {"date": date(2025, 4, 14), "name": "Vishu", "day": "Monday"},
            {"date": date(2025, 4, 18), "name": "Good Friday", "day": "Friday"},
            {"date": date(2025, 5, 1), "name": "May Day", "day": "Monday"},
            {"date": date(2025, 8, 15), "name": "Independence Day", "day": "Friday"},
            {"date": date(2025, 9, 5), "name": "Onam", "day": "Friday"},
            {"date": date(2025, 10, 2), "name": "Gandhi Jayanthi", "day": "Thursday"},
            {"date": date(2025, 12, 25), "name": "Christmas", "day": "Thursday"},
        ]

        for holiday in holidays:
            holiday_obj, created = Holiday.objects.get_or_create(
                date=holiday["date"],
                name=holiday["name"],
                day=holiday["day"]
            )
            self.stdout.write(f"{'Created' if created else 'Already exists'} holiday: {holiday['name']}")

        # Insert floating holidays
        floating_holidays = [
            {"name": "Maha Shivaratri", "date": date(2025, 2, 26)},
            {"name": "Holi", "date": date(2025, 3, 14)},
            {"name": "Ramzan", "date": date(2025, 3, 1)},
            {"name": "Ram Navami", "date": date(2025, 4, 6)},
            {"name": "Bakrid", "date": date(2025, 6, 6)}
        ]

        for holiday in floating_holidays:
            floating_holiday, created = FloatingHoliday.objects.get_or_create(
                name=holiday["name"],
                date=holiday["date"]
            )
            self.stdout.write(f"{'Created' if created else 'Already exists'} floating holiday: {holiday['name']}")

        self.stdout.write(self.style.SUCCESS("Data population completed successfully!"))
