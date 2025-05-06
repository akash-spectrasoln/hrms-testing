# employee_app/backends.py

from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from .models import Employees


class EmailBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to get the employee with the matching email
            employee = Employees.objects.get(personal_email=username)

            # Get the user associated with this employee
            user = get_user_model().objects.get(username=username)

            # Check if the provided password matches the user password
            if user.check_password(password):  # Django User's password check
                return user  # Return the Django User instance

        except (Employees.DoesNotExist, User.DoesNotExist):
            return None  # If no employee or user with that email exists

        return None

    def get_user(self, user_id):
        try:
            return get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            return None
