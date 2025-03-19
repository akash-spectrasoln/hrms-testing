from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings

class Command(BaseCommand):
    help = "Creates a superuser if one does not exist"

    def handle(self, *args, **kwargs):
        admin_username = settings.ADMIN_USERNAME
        admin_email = settings.ADMIN_EMAIL
        admin_password = settings.ADMIN_PASSWORD

        if not User.objects.filter(username=admin_username).exists():
            user = User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )
            user.is_staff = True  # Ensure the user is a staff member
            user.is_superuser = True  # Ensure the user is a superuser
            user.save()  # Save changes

            self.stdout.write(self.style.SUCCESS(f'Admin {admin_username} created successfully!'))
        else:
            self.stdout.write(self.style.WARNING('Admin already exists!'))
