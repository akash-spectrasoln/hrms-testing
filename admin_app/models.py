from django.db import models
from .models import *

import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from encryption.encryption import encrypt_field, decrypt_field 
from datetime import date
from django.utils import timezone


# Create your models here.


class Role(models.Model):
    role_id = models.CharField(max_length=100, unique=True, primary_key=True)

    role_name=models.CharField(max_length=50)

    def __str__(self):
        return self.role_name




class Country(models.Model):
    country_name = models.CharField(max_length=100)
    code = models.CharField(max_length=15,null=True)

    def __str__(self):
        return self.country_name


#
class state(models.Model):
    code=models.CharField(max_length=5,null=True)
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
from admin_app.utils import encrypt_employee_field,decrypt_employee_field
class EmployeeType(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
 # adjust if your policies are in a different file

class Employees(models.Model):
    EMPLOYEE_TYPE_CHOICES = [
        ('C-', 'Contractor'),
        ('I-', 'Intern'),
        ('E-', 'Employee'),
    ]
    STATUS_CHOICES = [
        ('employed', 'Employed'),
        ('resigned', 'Resigned'),
        ('Intern to employee','Intern to employee')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee_profile", null=True, blank=True)
    # employee_type = models.CharField(max_length=3, choices=EMPLOYEE_TYPE_CHOICES, verbose_name="Employee Type", null=True)
    employee_type = models.ForeignKey(EmployeeType, on_delete=models.SET_NULL, null=True, blank=True)
    employee_id = models.CharField(max_length=10, unique=True)
    old_employee_id=models.CharField(max_length=10, unique=True, null=True, blank=True)
    salutation = models.ForeignKey('Salutation', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, verbose_name="First Name")
    middle_name = models.CharField(max_length=50, verbose_name="Middle Name", blank=True,null=True,)
    last_name = models.CharField(max_length=50, verbose_name="Last Name")
    
    # company_email = models.EmailField(unique=True, verbose_name="Company Email")
    company_email = models.TextField(unique=True, verbose_name="Encrypted Company Email")
    personal_email = models.TextField(verbose_name="Personal Email")
    pm_email = models.EmailField(blank=True,null=True ,verbose_name="PM Email")
    mobile_phone = models.TextField()
    office_phone = models.CharField(max_length=15, blank=True,null=True,)
    home_phone = models.TextField(blank=True,null=True,)
    valid_from = models.TextField()
    valid_to = models.DateField()
    country = models.ForeignKey('Country', on_delete=models.CASCADE)
    state = models.ForeignKey('state', on_delete=models.CASCADE)
    address = models.TextField( blank=True,null=True,)
    house_name = models.TextField(null=True)# home_house
    home_post_office = models.TextField(null=True)
    home_city = models.TextField()
    pincode = models.TextField( blank=True,null=True,)
    role = models.ForeignKey('Role', on_delete=models.CASCADE, to_field="role_id", null=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.CASCADE)
    
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees_managed')
    employee_status = models.CharField(
    max_length=50,
    choices=STATUS_CHOICES,
    default='employed'
    )
    emergency_contact_name = models.TextField(null=True,blank=True)
    emergency_contact_phone = models.TextField(null=True,blank=True)
    emergency_contact_email = models.EmailField(null=True,blank=True)
    emergency_contact_relation = models.TextField(null=True,blank=True)
    base_salary = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    is_deleted = models.BooleanField(default=False)
    date_of_birth = models.TextField(null=True, blank=True, verbose_name="Date of Birth")
    # These two fields get dynamically assigned in save()
    # floating_holidays_balance = models.IntegerField(default=2)
    # floating_holidays_used = models.IntegerField(default=0)
    # total_leaves = models.PositiveIntegerField(default=15)
    # used_leaves = models.PositiveIntegerField(default=0) 

    password = models.CharField(max_length=128, null=True, blank=True)
    resignation_date = models.DateField(null=True, blank=True)
    # incentive = models.DecimalField(max_digits=10, decimal_places=2, default=0.0,null=True)
    incentive = models.TextField(null=True,blank=True)
    joining_bonus=models.TextField(null=True)
    pan_card = models.TextField(
         
        null=True, 
        blank=True, 
        verbose_name="PAN Card Number"
    )
    aadhaar = models.TextField(
       
        null=True, 
        blank=True, 
        verbose_name="Aadhaar Number"
    )
    bank_name = models.TextField(
        
        null=True, 
        blank=True, 
        verbose_name="Bank Name"
    )
    bank_branch = models.TextField(
        
        null=True, 
        blank=True, 
        verbose_name="Bank Branch"
    )
    bank_branch_address = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="Bank Branch Address"
    )
    bank_account = models.TextField(
        
        null=True, 
        blank=True, 
        verbose_name="Bank Account Number"
    )
    ifsc_code = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="IFSC Code"
    )
    # @property
    # def first_name(self):
    #     return decrypt_employee_field(self.first_name_e, self.employee_id, self.created_on or date.today())

    # @first_name.setter
    # def first_name(self, value):
    #     co = self.created_on or date.today()
    #     self.first_name_e = encrypt_employee_field(value, self.employee_id, co)

    # @property
    # def last_name(self):
    #     return decrypt_employee_field(self.last_name_e, self.employee_id, self.created_on or date.today())

    # @last_name.setter
    # def last_name(self, value):
    #     co = self.created_on or date.today()
    #     self.last_name_e = encrypt_employee_field(value, self.employee_id, co)

    # @property
    # def date_of_birth(self):
    #     return decrypt_employee_field(self.date_of_birth_e, self.employee_id, self.created_on or date.today())

    # @date_of_birth.setter
    # def date_of_birth(self, value):
    #     co = self.created_on or date.today()
    #     self.date_of_birth_e = encrypt_employee_field(str(value), self.employee_id, co)

    # @property
    # def personal_email(self):
    #     return decrypt_employee_field(self.personal_email_e, self.employee_id, self.created_on or date.today())

    # @personal_email.setter
    # def personal_email(self, value):
    #     co = self.created_on or date.today()
    #     self.personal_email_e = encrypt_employee_field(value, self.employee_id, co)

    # @property
    # def mobile_phone(self):
    #     return decrypt_employee_field(self.mobile_phone_e, self.employee_id, self.created_on or date.today())

    # @mobile_phone.setter
    # def mobile_phone(self, value):
    #     co = self.created_on or date.today()
    #     self.mobile_phone_e = encrypt_employee_field(value, self.employee_id, co)
    def available_leaves(self):
        return self.total_leaves - self.used_leaves

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
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

        # today = date.today()
        # experience_years = 0
        # if self.created_on:
        #     experience_years = (today - self.created_on.date()).days // 365

        # # --- Holiday policy lookup (for current year) ---
        # current_year = today.year
        # policy = HolidayPolicy.objects.filter(
        #     year=current_year,
        #     min_years_experience__lte=experience_years
        # ).order_by('-min_years_experience').first()

        # if policy:
        #     self.total_leaves = policy.ordinary_holidays_count + policy.extra_holidays
        # else:
        #     self.total_leaves = 0

        # # --- Floating holiday policy lookup (current year) ---
        # floating_policy = FloatingHolidayPolicy.objects.filter(year=current_year).first()
        # if floating_policy:
        #     self.floating_holidays_balance = floating_policy.allowed_floating_holidays

        super().save(*args, **kwargs)

        if is_new:
            current_year = date.today().year
            reset_period = HolidayResetPeriod.objects.filter(country=self.country).first()

            if not reset_period:
                raise Exception("Holiday reset period not configured for this country")

            start_month = reset_period.start_month
            start_day = reset_period.start_day

            financial_year_start_date = date(current_year, start_month, start_day)
            created_date = self.created_on or timezone.now()

            year_to_use = current_year - 1 if created_date.date() < financial_year_start_date else current_year

            LeaveDetails.objects.create(employee=self, year=year_to_use)


            
            # LeaveDetails.objects.create(employee=self)

    def __str__(self):
        return f"{self.employee_id} "



    # 
    @property
    def enc_valid_from(self):
        """Decrypt and return the valid_from."""
        decrypted_str = self._decrypt_field(self.valid_from)
        return datetime.strptime(decrypted_str, '%Y-%m-%d').date()

    @enc_valid_from.setter
    def enc_valid_from(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['valid_from'] = value
# ----
    @property
    def enc_date_of_birth(self):
        """Decrypt and return the date_of_birth."""
        decrypted_str = self._decrypt_field(self.date_of_birth)
        return datetime.strptime(decrypted_str, '%Y-%m-%d').date()

    @enc_date_of_birth.setter
    def enc_date_of_birth(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['date_of_birth'] = value


    @property
    def enc_house_name(self):
        """Decrypt and return the house_name."""
        return self._decrypt_field(self.house_name)

    @enc_house_name.setter
    def enc_house_name(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['house_name'] = value



    @property
    def enc_emergency_contact_relation(self):
        """Decrypt and return the emergency_contact_relation."""
        return self._decrypt_field(self.emergency_contact_relation)

    @enc_emergency_contact_relation.setter
    def enc_emergency_contact_relation(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['emergency_contact_relation'] = value



    @property
    def enc_incentive(self):
        """Decrypt and return the incentive."""
        return self._decrypt_field(self.incentive)

    @enc_incentive.setter
    def enc_incentive(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['incentive'] = value 


    @property
    def enc_joining_bonus(self):
        """Decrypt and return the joining_bonus."""
        return self._decrypt_field(self.joining_bonus)

    @enc_joining_bonus.setter
    def enc_joining_bonus(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['joining_bonus'] = value 


 

    @property
    def enc_emergency_contact_relation(self):
        """Decrypt and return the emergency_contact_relation."""
        return self._decrypt_field(self.emergency_contact_relation)

    @enc_emergency_contact_relation.setter
    def enc_emergency_contact_relation(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['emergency_contact_relation'] = value    


    @property
    def enc_ifsc_code(self):
        """Decrypt and return the ifsc_code."""
        return self._decrypt_field(self.ifsc_code)

    @enc_ifsc_code.setter
    def enc_ifsc_code(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['ifsc_code'] = value    


    @property
    def enc_bank_account(self):
        """Decrypt and return the bank_account."""
        decrypted_data=self._decrypt_field(self.bank_account)
        return decrypted_data

    @enc_bank_account.setter
    def enc_bank_account(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['bank_account'] = value    

    @property
    def enc_bank_branch_address(self):
        """Decrypt and return the bank_branch_address."""
        return self._decrypt_field(self.bank_branch_address)

    @enc_bank_branch_address.setter
    def enc_bank_branch_address(self, value):
        if value not in [None,""]:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['bank_branch_address'] = value

    @property
    def enc_bank_branch(self):
        """Decrypt and return the bank_branch."""
        return self._decrypt_field(self.bank_branch)

    @enc_bank_branch.setter
    def enc_bank_branch(self, value):
        if value not in [None,""]:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['bank_branch'] = value

    @property
    def enc_bank_name(self):
        """Decrypt and return the bank_name."""
        return self._decrypt_field(self.bank_name)

    @enc_bank_name.setter
    def enc_bank_name(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['bank_name'] = value



    @property
    def enc_aadhaar(self):
        """Decrypt and return the aadhaar."""
        return self._decrypt_field(self.aadhaar)

    @enc_aadhaar.setter
    def enc_aadhaar(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['aadhaar'] = value


    @property
    def enc_pan_card(self):
        """Decrypt and return the pan_card."""
        return self._decrypt_field(self.pan_card)

    @enc_pan_card.setter
    def enc_pan_card(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['pan_card'] = value


    @property
    def enc_base_salary(self):
        """Decrypt and return the base_salary."""
        return self._decrypt_field(self.base_salary)

    @enc_base_salary.setter
    def enc_base_salary(self, value):
        if value not in [None,""]:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['base_salary'] = value




    @property
    def enc_emergency_contact_phone(self):
        """Decrypt and return the emergency_contact_phone."""
        return self._decrypt_field(self.emergency_contact_phone)

    @enc_emergency_contact_phone.setter
    def enc_emergency_contact_phone(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['emergency_contact_phone'] = value

    
    @property
    def enc_pincode(self):
        """Decrypt and return the pincode."""
        decrypted_data=self._decrypt_field(self.pincode)
        return decrypted_data

    @enc_pincode.setter
    def enc_pincode(self, value):
        if value is not None:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['pincode'] = value  
    
    
    #
    @property
    def enc_emergency_contact_name(self):
        """Decrypt and return the emergency_contact_name."""
        return self._decrypt_field(self.emergency_contact_name)

    @enc_emergency_contact_name.setter
    def enc_emergency_contact_name(self, value):
        if not hasattr(self, '_fields_to_encrypt'):
            self._fields_to_encrypt = {}
        self._fields_to_encrypt['emergency_contact_name'] = value    
    
    #
    @property
    def enc_home_phone(self):
        """Decrypt and return the home_phone."""
        return self._decrypt_field(self.home_phone)

    @enc_home_phone.setter
    def enc_home_phone(self, value):
        if not hasattr(self, '_fields_to_encrypt'):
            self._fields_to_encrypt = {}
        self._fields_to_encrypt['home_phone'] = value

    #
    @property
    def enc_mobile_phone(self):
        """Decrypt and return the mobile_phone."""
        decrypted_data=self._decrypt_field(self.mobile_phone)
        return decrypted_data

    @enc_mobile_phone.setter
    def enc_mobile_phone(self, value):
        if not hasattr(self, '_fields_to_encrypt'):
            self._fields_to_encrypt = {}
        self._fields_to_encrypt['mobile_phone'] = value

    @property
    def enc_home_city(self):
        """Decrypt and return the home_city."""
        return self._decrypt_field(self.home_city)

    @enc_home_city.setter
    def enc_home_city(self, value):
        if not hasattr(self, '_fields_to_encrypt'):
            self._fields_to_encrypt = {}
        self._fields_to_encrypt['home_city'] = value

    @property
    def enc_personal_email(self):
        """Decrypt and return the personal_email."""
        return self._decrypt_field(self.personal_email)

    @enc_personal_email.setter
    def enc_personal_email(self, value):
        if not hasattr(self, '_fields_to_encrypt'):
            self._fields_to_encrypt = {}
        self._fields_to_encrypt['personal_email'] = value

    

    # @property
    # def enc_country(self):
    #     """Decrypt and return the company name."""
    #     return self._decrypt_field(self.country)

    # @enc_country.setter
    # def enc_country(self, value):

    #     """Temporarily store `cmp_name` for encryption during save."""
    #     if value is not None:
    #         self._data_to_encrypt = value  # Store the raw value temporarily
    #     else:
    #         self._data_to_encrypt = None
    #         self.country = None

    def _decrypt_field(self, encrypted_value):
        if encrypted_value:
            try:
                encrypted_value = json.loads(encrypted_value)
                (encrypted_data, nonce, tag, salt, original_type, iterations) = encrypted_value

                # Calculate created_day and incremented_value for decryption
                created_day = self.created_on.day  # Extract the day from the created_at timestamp
                incremented_value = self.id + created_day  # Combine cmp_id with created day

                # Use incremented_value for decryption
                return decrypt_field(
                    encrypted_data, incremented_value, nonce, tag, salt, original_type
                )
            except (ValueError, KeyError, TypeError) as e:
                print(f"Decryption error: {e}")
                return None
        return None

    


@receiver(post_save, sender=Employees)
def encrypt_data(sender, instance, created, **kwargs):
    if hasattr(instance, '_fields_to_encrypt'):  # Encrypt on both create and update
        created_day = instance.created_on.day
        incremented_value = instance.id + created_day

        for field_name, raw_value in instance._fields_to_encrypt.items():
            encrypted_data = encrypt_field(raw_value, incremented_value)
            setattr(instance, field_name, json.dumps(encrypted_data))

        # Avoid infinite recursion by saving without triggering signals again
        Employees.objects.filter(id=instance.id).update(
            **{field: getattr(instance, field) for field in instance._fields_to_encrypt}
        )



class LeaveDetails(models.Model):
    employee=models.ForeignKey(Employees,on_delete=models.CASCADE,related_name="emp_leave_details")
    floating_holidays_used = models.IntegerField(default=0)
    casual_leaves_used = models.IntegerField(default=0)
    year = models.IntegerField(null=True)
    total_casual_leaves=models.IntegerField(null=True , default=12)
    
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
class Holiday(models.Model): # this is the country based holiday
    date=models.DateField()
    name=models.CharField(max_length=100)
    day=models.CharField(max_length=50,null=True)
    year = models.IntegerField(default=datetime.now().year)
    country = models.ForeignKey('Country', on_delete=models.CASCADE)



class StateHoliday(models.Model): # this is the country based holiday
    date=models.DateField()
    name=models.CharField(max_length=100)
    year = models.IntegerField(default=datetime.now().year)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True)
    state = models.ForeignKey(state, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name



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
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    created_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='leave_requests_created')
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
        return f"Leave Request by {self.employee_master.first_name} from {self.start_date} to {self.end_date}"

    class Meta:
        verbose_name = "Leave Request"
        verbose_name_plural = "Leave Requests"


#floating holiday model is implemented below

from datetime import datetime
class FloatingHoliday(models.Model):
    name = models.CharField(max_length=100)  # e.g., New Year, Maha Shivaratri, etc.
    date = models.DateField()  # The specific date for the holiday
    year=models.IntegerField(default=datetime.now().year)
    country = models.ForeignKey('Country', on_delete=models.CASCADE)
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
    country = models.ForeignKey('Country', on_delete=models.CASCADE)

    def __str__(self):
        return (f"{self.year}: {self.ordinary_holidays_count} ordinary, "
                f"{self.min_years_experience}+ yrs = {self.extra_holidays} extra")

class FloatingHolidayPolicy(models.Model):
    """
    Stores the yearly policy for floating holidays.
    """
    year = models.PositiveIntegerField()
    allowed_floating_holidays = models.PositiveIntegerField(help_text="Number of floating holidays allowed this year.")
    country = models.ForeignKey('Country', on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.year}: {self.allowed_floating_holidays} floating holidays allowed"

class HolidayResetPeriod(models.Model):
    country = models.OneToOneField(Country, on_delete=models.CASCADE, related_name="holiday_reset")
    start_month = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 13)],
        help_text="Start month of holiday reset period"
    )
    start_day = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 32)],
        help_text="Start day of holiday reset period"
    )
    end_month = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 13)],
        help_text="End month of holiday reset period"
    )
    end_day = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 32)],
        help_text="End day of holiday reset period"
    )

    def __str__(self):
        return f"Holiday reset for {self.country.country_name}: {self.start_month}/{self.start_day} to {self.end_month}/{self.end_day}"
    
    