# employees/management/commands/encrypt_home_post_office.py
import json
from django.core.management.base import BaseCommand
from admin_app.models import Employees
from encryption.encryption import encrypt_field  

class Command(BaseCommand):
    help = "Encrypt existing plain-text home_post_office values in Employees table"

    def handle(self, *args, **kwargs):
        employees = Employees.objects.exclude(home_post_office__isnull=True).exclude(home_post_office="")

        updated_count = 0
        skipped_count = 0

        for emp in employees:
            try:
                # Check if already encrypted (JSON list of 6 elements: encrypted_data, nonce, tag, salt, type, iterations)
                try:
                    data = json.loads(emp.home_post_office)
                    if isinstance(data, list) and len(data) == 6:
                        skipped_count += 1
                        self.stdout.write(f"Skipping {emp.id} — already encrypted")
                        continue
                except json.JSONDecodeError:
                    pass  # It's plain text

                # Encrypt using same logic as model
                created_day = emp.created_on.day
                incremented_value = emp.id + created_day

                encrypted_data = encrypt_field(emp.home_post_office, incremented_value)
                emp.home_post_office = json.dumps(encrypted_data)
                emp.save(update_fields=['home_post_office'])

                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Encrypted home_post_office for Employee ID {emp.id}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing Employee ID {emp.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"Done! Encrypted: {updated_count}, Skipped: {skipped_count}"
        ))
