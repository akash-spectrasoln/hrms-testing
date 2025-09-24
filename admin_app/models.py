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

    class Meta:
        db_table='role' # this is for storing model name in database without app(django app) label 



class Country(models.Model):
    country_name = models.CharField(max_length=100)
    code = models.CharField(max_length=15,null=True)
    working_hours = models.PositiveIntegerField(default=9)

    def __str__(self):
        return self.country_name

    class Meta:
        db_table='country' # this is for storing model name in database without app(django app) label 

#
class state(models.Model):
    code=models.CharField(max_length=5,null=True)
    name=models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table='state' # this is for storing model name in database without app(django app) label 


class Salutation(models.Model):
    sal_name = models.CharField(max_length=50)

    def __str__(self):
        return self.sal_name

    class Meta:
        db_table='salutation' # this is for storing model name in database without app(django app) label 
    

class Department(models.Model):
    dep_name=models.CharField(max_length=100)

    def __str__(self):
        return self.dep_name
    
    class Meta:
        db_table='department' # this is for storing model name in database without app(django app) label 




from django.contrib.auth.hashers import make_password, check_password
import random

import re


from django.contrib.auth.models import User
from django.db import models
from datetime import date

class EmployeeType(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table='employeetype' # this is for storing model name in database without app(django app) label 


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
    employee_type = models.ForeignKey(EmployeeType, on_delete=models.SET_NULL, null=True, blank=True)
    employee_id = models.CharField(max_length=10, unique=True)
    old_employee_id=models.CharField(max_length=10, unique=True, null=True, blank=True)
    salutation = models.ForeignKey('Salutation', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, verbose_name="First Name")
    middle_name = models.CharField(max_length=50, verbose_name="Middle Name", blank=True,null=True,)
    last_name = models.CharField(max_length=50, verbose_name="Last Name")
    
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
    cost_center = models.ForeignKey('CostCenter',on_delete=models.SET_NULL,null=True,blank=True,related_name='employees')
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
    resignation_date = models.DateField(null=True, blank=True)
    incentive = models.TextField(null=True,blank=True)
    joining_bonus=models.TextField(null=True)
    hr_emails=models.BooleanField(default=False)
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
    excl_folup = models.BooleanField(default=False)

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


        super().save(*args, **kwargs)

        if is_new:
            # creating leavedetails record

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
    def enc_home_post_office(self):
        """Decrypt and return the home_post_office."""
        return self._decrypt_field(self.home_post_office)

    @enc_home_post_office.setter
    def enc_home_post_office(self, value):
        if value not in [None,""]:
            if not hasattr(self, '_fields_to_encrypt'):
                self._fields_to_encrypt = {}
            self._fields_to_encrypt['home_post_office'] = value




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

    class Meta:
        db_table='employees' # this is for storing model name in database without app(django app) label 
    


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
    employee = models.ForeignKey(Employees,on_delete=models.CASCADE,related_name="emp_leave_details")
    floating_holidays_used = models.IntegerField(default=0)
    casual_leaves_used = models.IntegerField(default=0)
    year = models.IntegerField(null=True)
    total_casual_leaves = models.IntegerField(null=True , default=12)
    planned_casual = models.IntegerField(null=True , default=0)
    planned_float = models.IntegerField(null=True , default=0)
    pending_casual = models.IntegerField(null=True , default=0)
    pending_float = models.IntegerField(null=True , default=0)

    class Meta:
        db_table='leavedetails' # this is for storing model name in database without app(django app) label 
    

#used to store employees for speciall access (example: employees to recieve birthday emails)
class Communication(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="communication_type", null=True, blank=True)
    type = models.CharField(max_length=50,default="HR NOTIFICATION")

    class Meta:
        db_table='communication'

# used to store company utility details (Bank acc, transaction type etc)
class SetUpTable(models.Model):
    field = models.CharField(max_length=30)
    value = models.CharField(max_length=30)

    class Meta:
        db_table='setuptable'
    
    
class Resume(models.Model):
    employee = models.ForeignKey(Employees, related_name='resumes', on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} for {self.employee.first_name} {self.employee.last_name}"

    class Meta:
        db_table='resume' # this is for storing model name in database without app(django app) label 
    


class Certificate(models.Model):
    employee = models.ForeignKey(Employees, related_name='certificates', on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/certificates/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} for {self.employee.first_name} {self.employee.last_name}"

    class Meta:
        db_table='certificate'


from datetime import datetime
class Holiday(models.Model): # this is the country based holiday
    date=models.DateField()
    name=models.CharField(max_length=100)
    day=models.CharField(max_length=50,null=True)
    year = models.IntegerField(default=datetime.now().year)
    country = models.ForeignKey('Country', on_delete=models.CASCADE)

    class Meta:
        db_table='holiday'



class StateHoliday(models.Model): # this is the country based holiday
    date=models.DateField()
    name=models.CharField(max_length=100)
    year = models.IntegerField(default=datetime.now().year)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True)
    state = models.ForeignKey(state, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table='stateholiday'



# below is the leave request model


from django.db import models
from django.contrib.auth.models import User  # Assuming employee is a User model
from .models import Holiday



class LeaveRequest(models.Model):


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


        super().save(*args, **kwargs)


    def calculate_total_days(self):
        """Calculate the total number of days for this leave request."""
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"Leave Request by {self.employee_master.first_name} from {self.start_date} to {self.end_date}"

    class Meta:
        verbose_name = "Leave Request"
        verbose_name_plural = "Leave Requests"
        db_table='leaverequest'


#floating holiday model is implemented below

from datetime import datetime
class FloatingHoliday(models.Model):
    name = models.CharField(max_length=100)  # e.g., New Year, Maha Shivaratri, etc.
    date = models.DateField()  # The specific date for the holiday
    year=models.IntegerField(default=datetime.now().year)
    country = models.ForeignKey('Country', on_delete=models.CASCADE)
    def __str__(self):
        return self.name

    class Meta:
        db_table='floatingholiday'


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
    
    class Meta:
        db_table='holidaypolicy'

class FloatingHolidayPolicy(models.Model):
    """
    Stores the yearly policy for floating holidays.
    """
    year = models.PositiveIntegerField()
    allowed_floating_holidays = models.PositiveIntegerField(help_text="Number of floating holidays allowed this year.")
    country = models.ForeignKey('Country', on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.year}: {self.allowed_floating_holidays} floating holidays allowed"
    
    class Meta:
        db_table='floatingholidaypolicy'

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
    

    class Meta:
        db_table='holidayresetperiod'



class Client(models.Model):
    """
    Stores client details including name, alias, address, and country.
    """
    client_id = models.AutoField(primary_key=True)
    client_name = models.CharField(max_length=100)
    client_alias = models.CharField(max_length=20, unique=True)
    client_addr = models.CharField(max_length=255)
    country = models.ForeignKey(
        'Country',
        on_delete=models.PROTECT,  # prevent accidental deletion
        related_name='clients'
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'Employees',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients_created"
    )
    updated_by = models.ForeignKey(
        'Employees',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients_updated"
    )
    from django.utils import timezone

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = 'client'
        ordering = ['client_name']
        indexes = [
            models.Index(fields=['client_alias']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return self.client_name

     
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Project(models.Model):
    """
    Project model to track projects under specific clients.
    Includes validity range, active status, manager assignment, and soft deletion support.

    Business Rules:
    - Current project: valid_from <= today <= valid_to (or valid_to is null) => is_active=True
    - Expired project: valid_to < today => is_active=False
    - Future project: valid_from > today => is_active=False
    """

    project_id = models.AutoField(primary_key=True)
    project_name = models.CharField(max_length=255)
    project_desc = models.TextField(
        verbose_name="Project Description",
        blank=True,
        null=True
    )

    valid_from = models.DateField()
    valid_to = models.DateField()

    client = models.ForeignKey(
        'Client',
        on_delete=models.CASCADE,
        related_name='projects'
    )

    prj_manager = models.ForeignKey(
        'Employees',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_projects',
        verbose_name="Project Manager"
    )

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    # Optional audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ✅ New fields
    created_by = models.ForeignKey(
        'Employees',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects_created"
    )
    updated_by = models.ForeignKey(
        'Employees',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects_updated"
    )

    class Meta:
        db_table = 'project'
        ordering = ['-valid_from']
        constraints = [
            models.CheckConstraint(
                check=models.Q(valid_from__lte=models.F('valid_to')),
                name='valid_date_range_check'
            ),
            models.UniqueConstraint(
                fields=['project_name', 'client'],
                name='unique_project_per_client'
            ),
        ]
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['client']),
            models.Index(fields=['valid_to']),
        ]

    def clean(self):
        """Ensure valid_from <= valid_to."""
        super().clean()
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValidationError({
                'valid_to': 'Valid To date must be on or after Valid From date.'
            })

    def save(self, *args, **kwargs):
        """
        Override save() to automatically set is_active based on project validity:
        - Current project: is_active=True
        - Expired or future: is_active=False
        """
        today = timezone.now().date()

        if self.valid_from > today:
            self.is_active = False  # future project
        elif self.valid_to < today:
            self.is_active = False  # expired project
        else:
            self.is_active = True   # current project

        super().save(*args, **kwargs)

    @property
    def status(self):
        """
        Returns project status as one of:
        - 'current'  -> active project within validity dates
        - 'expired'  -> valid_to has passed
        - 'future'   -> valid_from is in the future
        """
        today = timezone.now().date()
        if self.valid_from > today:
            return "future"
        elif self.valid_to < today:
            return "expired"
        return "current"

    def soft_delete(self):
        """Marks the project as inactive instead of deleting it."""
        self.is_deleted= True
        self.save(update_fields=['is_deleted'])

    def restore(self):
        """Restores the project to active state."""
        self.is_active = True
        self.save(update_fields=['is_active'])

    def __str__(self):
        return f"{self.client.client_alias}-{self.project_name} "

    def is_expired(self):
        """Returns True if the project's valid_to date has passed."""
        return self.valid_to < timezone.now().date()

    def auto_expire_if_needed(self):
        """Deactivates the project if its valid_to date is in the past."""
        if self.is_active and self.is_expired():
            self.is_active = False
            self.save(update_fields=['is_active'])

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q


class AssignProject(models.Model):
    """
    Links an employee to a project assignment with date validation and overlap prevention.
    """
    emp_prj_id = models.AutoField(primary_key=True)

    employee = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name='project_assignments'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='employee_assignments'
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    designation = models.CharField(
        max_length=100,
        verbose_name="Designation in Project",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(
    'Employees',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
        related_name="assignments_created"
    )
    updated_by = models.ForeignKey(
        'Employees',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments_updated"
    )


    class Meta:
        unique_together = ('employee', 'project', 'start_date')
        ordering = ['-start_date']
        verbose_name = "Assigned Project"
        verbose_name_plural = "Assigned Projects"
        db_table = 'assignproject'
        indexes = [
            models.Index(fields=['employee', 'project']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
    def save(self, *args, **kwargs):
        """
        Override save() to automatically set is_active based on project validity:
        - Current project: is_active=True
        - Expired or future: is_active=False
        """
        today = timezone.now().date()

        if self.start_date > today:
            self.is_active = False  # future project
        elif self.end_date < today:
            self.is_active = False  # expired project
        else:
            self.is_active = True   # current project

        super().save(*args, **kwargs)

    def clean(self):
        project = getattr(self, 'project', None)

        if project:
            if self.start_date and self.start_date < project.valid_from:
                raise ValidationError({
                    'start_date': f"Start date cannot be before project validity ({project.valid_from})."
                })
            if self.end_date and self.end_date > project.valid_to:
                raise ValidationError({
                    'end_date': f"End date cannot be after project validity ({project.valid_to})."
                })

        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': "End date cannot be before start date."
            })

        # Check overlapping assignments
        if self.employee and self.project and self.start_date:
            qs = AssignProject.objects.filter(
                employee=self.employee,
                project=self.project
            ).exclude(pk=self.pk)

            if self.end_date:
                qs = qs.filter(
                    start_date__lte=self.end_date
                ).filter(
                    Q(end_date__isnull=True) | Q(end_date__gte=self.start_date)
                )
            else:
                qs = qs.filter(
                    Q(end_date__isnull=True) | Q(end_date__gte=self.start_date)
                )

            if qs.exists():
                raise ValidationError(
                    "This employee is already assigned to this project in the selected date range."
                )

    def __str__(self):
        return f"{self.employee} -> {self.project} from {self.start_date}"

class Activity(models.Model):

    act_id = models.AutoField(primary_key=True)
    act_name = models.CharField(max_length=100)
    class Meta:
        db_table='activity'

class WrkLocation(models.Model):  

    loc_id = models.AutoField(primary_key=True)
    loc_name = models.CharField(max_length=100)
    class Meta:
        db_table='wrklocation'
class CostCenter(models.Model):
    costcenter_id = models.CharField(
        max_length=10,
        primary_key=True,
        editable=False
    )
    costcenter_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    class Meta:
        db_table='costcenter'

    def save(self, *args, **kwargs):
        if not self.costcenter_id:
            last = CostCenter.objects.order_by('-costcenter_id').first()
            if last and last.costcenter_id[2:].isdigit():
                last_num = int(last.costcenter_id[2:])
                next_num = last_num + 1
            else:
                next_num = 1
            self.costcenter_id = f"CC{next_num:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.costcenter_id} - {self.costcenter_name}"


from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q
from django.utils import timezone

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.utils import timezone



from datetime import timedelta
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator



class TimesheetHdr(models.Model):
    tsheet_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name="timesheet_headers")
    week_start = models.DateField()  # Monday
    week_end = models.DateField()    # Sunday
    tot_hrs_wrk = models.IntegerField(default=0)
    tot_hol_hrs = models.IntegerField(default=0)
    tot_lev_hrs = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_delayed = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(Employees, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_timesheets")
    
    class Meta:
        db_table='timesheet_hdr'

    def check_delayed_status(self):
        # Deadline = Monday after week_end, end of day
        deadline = timezone.datetime.combine(
            self.week_end + timedelta(days=1),  # Monday
            timezone.datetime.max.time()        # 23:59:59
        )
        deadline = timezone.make_aware(deadline)

        now = timezone.now()

        # Delayed if created/updated after deadline
        self.is_delayed = now > deadline and (self.created_at > deadline or self.updated_at > deadline)
        self.save(update_fields=["is_delayed"])



    def recalc_totals(self):
        work_hours_per_day = getattr(self.employee.country, "working_hours", 9)
        items = list(self.timesheet_items.all())
        self.tot_hrs_wrk = 0
        self.tot_hol_hrs = 0
        self.tot_lev_hrs = 0
        date_range_start = self.week_start
        date_range_end = self.week_end

        holidays = set(Holiday.objects.filter(
            country=self.employee.country,
            date__range=(date_range_start, date_range_end)
        ).values_list('date', flat=True))

        state_holidays = set(StateHoliday.objects.filter(
            country=self.employee.country,
            state=self.employee.state,
            date__range=(date_range_start, date_range_end)
        ).values_list('date', flat=True))

        all_holidays = holidays | state_holidays

        current_date = self.week_start
        while current_date <= self.week_end:
            day_items = [i for i in items if i.wrk_date == current_date]
            total_daily_work_hours = sum(i.wrk_hours for i in day_items)

            # Check if the day is a weekend (Saturday = 5, Sunday = 6)
            is_weekend = current_date.weekday() >= 5
            
            is_holiday = current_date in all_holidays
            is_leave = LeaveRequest.objects.filter(
                employee_master=self.employee,
                start_date__lte=current_date,
                end_date__gte=current_date,
                status="Approved"
            ).exists()

            if is_holiday:
                if total_daily_work_hours > 0:
                    # Employee worked on holiday → count only as work hours
                    self.tot_hrs_wrk += total_daily_work_hours
                else:
                    # Employee didn’t work → count as holiday hours
                    self.tot_hol_hrs += work_hours_per_day
            elif is_leave and not is_weekend:
                # Leave day logic, but only if it's not a weekend
                self.tot_lev_hrs += work_hours_per_day
            else:
                # Regular weekday or weekend logic
                self.tot_hrs_wrk += total_daily_work_hours

            
            current_date += timedelta(days=1)
        
        self.save(update_fields=["tot_hrs_wrk", "tot_hol_hrs", "tot_lev_hrs"])
    
    def __str__(self):
        return f"Timesheet {self.tsheet_id} - {self.employee.first_name}{self.employee.middle_name}{self.employee.last_name}"


class TimesheetItem(models.Model):
    id = models.AutoField(primary_key=True)
    hdr = models.ForeignKey(TimesheetHdr, on_delete=models.CASCADE, related_name="timesheet_items")
    wrk_date = models.DateField()
    project_assignment = models.ForeignKey(AssignProject, on_delete=models.CASCADE, related_name="timesheet_items",null=True,
    blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, editable=False,null=True,
    blank=True)
    costcenter = models.ForeignKey(CostCenter, on_delete=models.CASCADE,null=True,
    blank=True)
    wrk_hours = models.IntegerField()
    activity = models.ForeignKey(
        'Activity', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='timesheets'
    )
    work_location = models.ForeignKey(
        'WrkLocation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='timesheets'
    )
    description = models.TextField(blank=True)

    class Meta:
        db_table='timesheetitem'

    def save(self, *args, **kwargs):
        # Set project from assignment
        if self.project_assignment:
            self.project = self.project_assignment.project

        super().save(*args, **kwargs)

        # Update totals & delayed status
        self.hdr.recalc_totals()
        self.hdr.check_delayed_status()

    def delete(self, *args, **kwargs):
        hdr = self.hdr
        super().delete(*args, **kwargs)
        hdr.recalc_totals()

    def __str__(self):
        return f"Item {self.id} - {self.project.project_name} ({self.date})"
    

class DeviceBrand(models.Model):
    id = models.AutoField(primary_key=True)
    device_brand = models.CharField(max_length=100, unique=True)   # Lenovo, HP, Acer, Dell

    class Meta:
        db_table = "device_brand"

    def __str__(self):
        return self.device_brand


class DeviceType(models.Model):
    id = models.AutoField(primary_key=True)
    device_type = models.CharField(max_length=50, unique=True)   # Laptop, Mouse

    class Meta:
        db_table = "device_type"

    def __str__(self):
        return self.device_type


class Devices(models.Model):
    id = models.AutoField(primary_key=True)
    device_model = models.CharField(max_length=100)   # Device model
    device_type = models.ForeignKey(DeviceType, on_delete=models.CASCADE, db_column="type")
    device_brand = models.ForeignKey(DeviceBrand, on_delete=models.CASCADE, db_column="brand")
    serial_no = models.CharField(max_length=100, unique=True)
    proc_date = models.DateField()   # Procurement Date
    retire_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "devices"

    def __str__(self):
        return f"{self.device_brand.device_brand} {self.device_model} ({self.serial_no})"
    def save(self, *args, **kwargs):
        # Automatically set active based on retire_date
        if self.retire_date:
            self.active = False
        else:
            self.active = True
        super().save(*args, **kwargs)
    @property
    def is_available(self):
        """Check if device is active and not retired & not currently assigned."""
        return (
            self.active
            and self.retire_date is None
            and not self.device_trackers.filter(end_date__isnull=True).exists()
        )

class DeviceTracker(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        "Employees",
        on_delete=models.CASCADE,
        related_name="device_trackers"
    )
    device = models.ForeignKey(
        "Devices",
        on_delete=models.CASCADE,
        related_name="device_trackers"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "device_tracker"
        constraints = [
            # Prevent one device from being assigned to multiple employees at once
            models.UniqueConstraint(
                fields=["device"],
                condition=Q(end_date__isnull=True),
                name="unique_active_device_assignment",
            )
        ]

    def clean(self):
        """Validate assignment rules before saving."""
        from django.core.exceptions import ValidationError

        # Validate date logic
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError("End date cannot be earlier than start date.")

        # 🚨 Prevent duplicate active device assignment
        if self.device_id and not self.end_date:  # means still active
            existing = DeviceTracker.objects.filter(
                device=self.device,
                end_date__isnull=True
            ).exclude(pk=self.pk)  # exclude self if updating
            if existing.exists():
                raise ValidationError(
                    f"Device {self.device} is already assigned to {existing.first().employee.first_name} {existing.first().employee.last_name}."
                )

        # 🚨 Prevent same employee having 2 active devices of same type
        if self.device_id and not self.end_date:
            same_type_active = DeviceTracker.objects.filter(
                employee=self.employee,
                device__device_type=self.device.device_type,
                end_date__isnull=True,
            ).exclude(pk=self.pk)
            if same_type_active.exists():
                raise ValidationError(
                    f"{self.employee.first_name} already has an active {self.device.device_type} assigned."
                )
