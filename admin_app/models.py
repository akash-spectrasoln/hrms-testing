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
class Employees(models.Model):
    # Define Employee Types
    EMPLOYEE_TYPE_CHOICES = [
        ('C-', 'Contractor'),
        ('I-', 'Intern'),
        ('E-', 'Employee'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee_profile", null=True, blank=True)

    # Employee Type Field
    employee_type = models.CharField(max_length=3, choices=EMPLOYEE_TYPE_CHOICES, verbose_name="Employee Type",null=True)


    emp_id=models.CharField(max_length=10,unique=True)
    sal=models.ForeignKey(Salutation,on_delete=models.CASCADE)
    emp_fname=models.CharField(max_length=50,verbose_name="Employee First Name")
    emp_mname=models.CharField(max_length=50,verbose_name="Employee Middle Name")
    emp_lname=models.CharField(max_length=50,verbose_name="Employee Last Name")
    emp_email = models.EmailField(unique=True,verbose_name="Company Email")

    emp_pemail=models.EmailField(verbose_name="Personal Email")
    emp_mob_ph=models.CharField(max_length=15)
    emp_off_ph=models.CharField(max_length=15)
    emp_home_ph=models.CharField(max_length=15)
    emp_val_from = models.DateField()
    emp_val_to = models.DateField()
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    state = models.ForeignKey(state, on_delete=models.CASCADE)
    emp_addr=models.CharField(max_length=150,null=True)
    emp_home_street=models.TextField()
    emp_home_city=models.TextField()
    pincode=models.CharField(max_length=10,null=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, to_field="role_id", null=True, blank=True)

    dep = models.ForeignKey(Department, on_delete=models.CASCADE)
    designation = models.CharField(max_length=100)
    employee_manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='employees_managed')
    employee_status = models.CharField(max_length=10)
    # Self-referencing ForeignKey to link the employee to a manager (another employee)
    emp_cp_name = models.CharField(max_length=100)
    emp_cp_ph = models.CharField(max_length=15)
    emp_cp_email = models.EmailField()
    emp_cp_relation = models.CharField(max_length=100)
    emp_base = models.DecimalField(max_digits=10, decimal_places=2)

    emp_resume=models.FileField(upload_to='documents/',null=True,blank=True)
    emp_certif=models.FileField(upload_to='documents/',null=True , blank=True)
    created_on=models.DateTimeField(auto_now_add=True,null=True)
    modified_on=models.DateTimeField(auto_now=True,null=True)
    is_delete = models.BooleanField(default=False)  # New field for soft delete
    floating_holidays_balance = models.IntegerField(default=2)  # Each employee has 2 floating holidays
    floating_holidays_used = models.IntegerField(default=0)  # Tracks used floating holidays
    emp_total_leaves = models.PositiveIntegerField(default=15)  # Total number of leaves
    emp_used_leaves = models.PositiveIntegerField(default=0)  # Leaves already used
    emp_password = models.CharField(max_length=128, null=True, blank=True)  # Allows existing records to remain valid

    def available_leaves(self):
        return self.emp_total_leaves - self.emp_used_leaves  # Calculate available leaves

    def delete(self, *args, **kwargs):
        """Perform a soft delete by setting is_delete to True."""
        self.is_delete = True
        self.save()

    # New fields to track the admin user who created and modified the record
    # created_by = models.ForeignKey(User, related_name='created_employees', on_delete=models.SET_NULL, null=True)
    # modified_by = models.ForeignKey(User, related_name='modified_employees', on_delete=models.SET_NULL, null=True)


    def save(self, *args, **kwargs):


        if not self.user:
            self.user, created = User.objects.get_or_create(
                username=self.emp_email,
                defaults={'email': self.emp_email, 'password': 'defaultpassword'}
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.emp_id} ({self.get_employee_type_display()})"

#
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

