from django.db import models
from .models import *


# Create your models here.


class Role(models.Model):
    role_id = models.CharField(max_length=100, unique=True, primary_key=True)

    role_name=models.CharField(max_length=50)

    def __str__(self):
        return self.role_name




class Country(models.Model):
    country_name = models.CharField(max_length=100)


    def __str__(self):
        return self.country_name


#
class state(models.Model):
    name=models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")

    def __str__(self):
        return self.name


class Salutation(models.Model):
    sal_name = models.CharField(max_length=50)

    def __str__(self):
        return self.sal_name

class Department(models.Model):
    dep_name=models.CharField(max_length=100)

    def __str__(self):
        return self.dep_name




from django.contrib.auth.hashers import make_password, check_password
import random

import re


from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User

from django.db import models
from django.contrib.auth.models import User
from datetime import date

 # adjust if your policies are in a different file

class Employees(models.Model):
    EMPLOYEE_TYPE_CHOICES = [
        ('C-', 'Contractor'),
        ('I-', 'Intern'),
        ('E-', 'Employee'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee_profile", null=True, blank=True)
    employee_type = models.CharField(max_length=3, choices=EMPLOYEE_TYPE_CHOICES, verbose_name="Employee Type", null=True)
    employee_id = models.CharField(max_length=10, unique=True)
    salutation = models.ForeignKey('Salutation', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, verbose_name="First Name")
    middle_name = models.CharField(max_length=50, verbose_name="Middle Name", blank=True)
    last_name = models.CharField(max_length=50, verbose_name="Last Name")
    company_email = models.EmailField(unique=True, verbose_name="Company Email")
    personal_email = models.EmailField(verbose_name="Personal Email")
    mobile_phone = models.CharField(max_length=15)
    office_phone = models.CharField(max_length=15, blank=True)
    home_phone = models.CharField(max_length=15, blank=True)
    valid_from = models.DateField()
    valid_to = models.DateField()
    country = models.ForeignKey('Country', on_delete=models.CASCADE)
    state = models.ForeignKey('state', on_delete=models.CASCADE)
    address = models.CharField(max_length=150, blank=True)
    home_house = models.TextField()
    home_post_office = models.TextField()
    home_city = models.TextField()
    pincode = models.CharField(max_length=10, blank=True)
    role = models.ForeignKey('Role', on_delete=models.CASCADE, to_field="role_id", null=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.CASCADE)
    designation = models.CharField(max_length=100)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees_managed')
    employee_status = models.CharField(max_length=10)
    emergency_contact_name = models.CharField(max_length=100,null=True)
    emergency_contact_phone = models.CharField(max_length=15,null=True)
    emergency_contact_email = models.EmailField(null=True)
    emergency_contact_relation = models.CharField(max_length=100,null=True,blank=True)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    is_deleted = models.BooleanField(default=False)

    # These two fields get dynamically assigned in save()
    floating_holidays_balance = models.IntegerField(default=2)
    floating_holidays_used = models.IntegerField(default=0)
    total_leaves = models.PositiveIntegerField(default=15)
    used_leaves = models.PositiveIntegerField(default=0)

    password = models.CharField(max_length=128, null=True, blank=True)
    resignation_date = models.DateField(null=True, blank=True)
    incentive = models.DecimalField(max_digits=10, decimal_places=2, default=0.0,null=True)

    def available_leaves(self):
        return self.total_leaves - self.used_leaves

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def save(self, *args, **kwargs):
        if not self.user:
            # Create the user without a password first
            self.user, created = User.objects.get_or_create(
                username=self.company_email,
                defaults={'email': self.company_email}
            )
            if created:
                # Set the hashed default password
                self.user.set_password('defaultpassword')
                self.user.save()
        else:
            # Optionally, if `password` field is set on Employees, allow user password update.
            if self.password:
                self.user.set_password(self.password)
                self.user.save()
                # Clear the password field (optional: prevents storing plain text)
                self.password = None

        today = date.today()
        experience_years = 0
        if self.created_on:
            experience_years = (today - self.created_on.date()).days // 365

        # --- Holiday policy lookup (for current year) ---
        current_year = today.year
        policy = HolidayPolicy.objects.filter(
            year=current_year,
            min_years_experience__lte=experience_years
        ).order_by('-min_years_experience').first()

        if policy:
            self.total_leaves = policy.ordinary_holidays_count + policy.extra_holidays
        else:
            self.total_leaves = 0

        # --- Floating holiday policy lookup (current year) ---
        floating_policy = FloatingHolidayPolicy.objects.filter(year=current_year).first()
        if floating_policy:
            self.floating_holidays_balance = floating_policy.allowed_floating_holidays

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} ({self.get_employee_type_display()})"


class Resume(models.Model):
    employee = models.ForeignKey(Employees, related_name='resumes', on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} for {self.employee.first_name} {self.employee.last_name}"


class Certificate(models.Model):
    employee = models.ForeignKey(Employees, related_name='certificates', on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/certificates/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} for {self.employee.first_name} {self.employee.last_name}"
# leave management section

from datetime import datetime
class Holiday(models.Model):
    date=models.DateField(unique=True)
    name=models.CharField(max_length=100)
    day=models.CharField(max_length=50,null=True)
    year = models.IntegerField(default=datetime.now().year)


#
# below is the leave request model


from django.db import models
from django.contrib.auth.models import User  # Assuming employee is a User model
from .models import Holiday
from .utils import calculate_leave_days  # Import the function from utils page


class LeaveRequest(models.Model):
    # LEAVE_TYPES = [
    #     ('CL', 'Casual Leave'),
    #     ('SL', 'Sick Leave'),
    #     ('EL', 'Earned Leave'),
    #     ('PL', 'Parental Leave'),
    #     ('ML', 'Maternity Leave'),
    #     ('UL', 'Unpaid Leave'),
    # ]

    LEAVE_TYPES = [
        ('Floating Leave', 'Floating Leave'),
        ('Casual Leave', 'Casual Leave'),
    ]
    employee_user = models.ForeignKey(User, on_delete=models.CASCADE)  # Reference to the employee (User model)
    employee_master = models.ForeignKey(Employees, on_delete=models.CASCADE,related_name='leave_requests',null=True)  # Reference to Employees model
    start_date = models.DateField()  # Start date of the leave
    end_date = models.DateField()    # End date of the leave
    reason = models.TextField()      # Reason for the leave
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES, default='Casual Leave')  # Type of leave
    status = models.CharField(max_length=20, default="Pending")  # Leave request status (e.g., Pending, Approved)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,related_name='approved_leaves')
    leave_days = models.PositiveIntegerField(null=True, blank=True)  # Field to store the calculated leave days


    #this method calculates the total no of laeves for the request
    # def available_leaves(self):
    #     return self.emp_total_leaves - self.emp_used_leaves  # Calculate available leaves

    def available_leaves(self):
        return self.employee_master.emp_total_leaves - self.employee_master.emp_used_leaves

    def save(self, *args, **kwargs):
        print("Saving Leave Request...")  # Add a print statement to check if save method is called
        if not self.leave_days:
            # Fetch holidays and floating holidays
            holidays = list(Holiday.objects.values_list('date', flat=True))  # List of holiday dates
            floating_holidays = list(
                FloatingHoliday.objects.values_list('date', flat=True))  # List of floating holiday dates


            # Print fetched holidays and floating holidays
            print("Holidays: ", holidays)
            print("Floating Holidays: ", floating_holidays)

            # Calculate leave days
            self.leave_days = calculate_leave_days(
                start_date=self.start_date,
                end_date=self.end_date,
                holidays=holidays,
                floating_holidays=floating_holidays,
            )

        super().save(*args, **kwargs)


    def calculate_total_days(self):
        """Calculate the total number of days for this leave request."""
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"Leave Request by {self.employee.username} from {self.start_date} to {self.end_date}"

    class Meta:
        verbose_name = "Leave Request"
        verbose_name_plural = "Leave Requests"


#floating holiday model is implemented below

from datetime import datetime
class FloatingHoliday(models.Model):
    name = models.CharField(max_length=100)  # e.g., New Year, Maha Shivaratri, etc.
    date = models.DateField()  # The specific date for the holiday
    year=models.IntegerField(default=datetime.now().year)

    def __str__(self):
        return self.name


class HolidayPolicy(models.Model):
    """
    Stores the yearly policy for company-wide ordinary holidays and experience-based extra holidays.
    """
    year = models.PositiveIntegerField()
    ordinary_holidays_count = models.PositiveIntegerField(help_text="Total ordinary holidays for the year.")
    min_years_experience = models.PositiveIntegerField(help_text="Minimum years of experience for extra holidays to apply.")
    extra_holidays = models.PositiveIntegerField(help_text="Extra holidays allocated for experience.")

    def __str__(self):
        return (f"{self.year}: {self.ordinary_holidays_count} ordinary, "
                f"{self.min_years_experience}+ yrs = {self.extra_holidays} extra")

class FloatingHolidayPolicy(models.Model):
    """
    Stores the yearly policy for floating holidays.
    """
    year = models.PositiveIntegerField(unique=True)
    allowed_floating_holidays = models.PositiveIntegerField(help_text="Number of floating holidays allowed this year.")

    def __str__(self):
        return f"{self.year}: {self.allowed_floating_holidays} floating holidays allowed"