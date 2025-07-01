from django import forms
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.utils import timezone
import random
import os
import logging
from .models import Employees, Country, state, Salutation, Role, Department,Resume,Certificate

logger = logging.getLogger(__name__)

import os
from django import forms
from django.core.exceptions import ValidationError
from .models import Employees, Resume, Certificate, Country, state

import os
from django import forms
from django.core.exceptions import ValidationError
from .models import Employees, Country, state  # Import your models here

STATUS_CHOICES = (
    ('employed', 'Employed'),
    ('resigned', 'Resigned'),
    ('maternal_leave', 'Maternal Leave'),
)

import os
from django import forms
from django.core.exceptions import ValidationError
from .models import Employees, Country, state, EmployeeType  # Adjust imports accordingly


class EmployeeEditForm(forms.ModelForm):
    
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=False,
        empty_label="Select a Country"
    )
    state = forms.ModelChoiceField(
        queryset=state.objects.none(),
        required=False,
        empty_label="Select a State"
    )
    house_name = forms.CharField(required=False)
     # assuming you have STATUS_CHOICES constant
    middle_name = forms.CharField(required=False)
    office_phone = forms.CharField(required=False)
    home_phone = forms.CharField(required=False)
    home_city = forms.CharField(required=False)
    emergency_contact_email=forms.EmailField(required=False)
    
    incentive = forms.CharField(required=False)
    joining_bonus = forms.CharField(required=False)
    home_post_office = forms.CharField(required=False)
    manager = forms.ModelChoiceField(
        queryset=Employees.objects.all(),
        required=False,
        empty_label="None"
    )
    # Changed employee_type from ChoiceField to ModelChoiceField for FK relation
    # employee_type = forms.ModelChoiceField(
    #     queryset=EmployeeType.objects.all(),
    #     required=True,
    #     widget=forms.Select(attrs={'class': 'form-control'})
    # )
    resignation_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    resumes = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'multiple': True}))
    certificates = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'multiple': True}))
    
    date_of_birth = forms.DateField(
        required=True,  # or False if optional
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date of Birth"
    )
    emergency_contact_phone=forms.CharField(required=False)
    emergency_contact_name=forms.CharField(required=False)
    pan_card = forms.CharField(
        required=False, 
        max_length=20,
        label="PAN Card"
    )
    aadhaar = forms.CharField(
        required=False,
        max_length=20,
        label="Aadhaar"
    )
    bank_name = forms.CharField(
        required=True,
        max_length=100,
        label="Bank Name"
    )
    bank_branch = forms.CharField(
        required=False,
        max_length=100,
        label="Bank Branch"
    )
    bank_branch_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label="Bank Branch Address"
    )
    bank_account = forms.CharField(
        required=True,
        max_length=30,
        label="Bank Account"
    )
    ifsc_code = forms.CharField(
        required=True,
        max_length=15,
        label="IFSC Code"
    )

    # ... rest of fields and widgets remain as before ...

    class Meta:
        model = Employees
        fields = [
            'employee_id', 'old_employee_id','salutation', 'first_name', 'middle_name', 'last_name',
            'company_email', 'personal_email', 'mobile_phone', 'office_phone','home_post_office',
            'home_phone', 'valid_from', 'valid_to', 'country', 'state', 
            'department', 'role', 'manager','home_city','pincode','emergency_contact_name','emergency_contact_phone','emergency_contact_email',
             'emergency_contact_relation',
             'base_salary',#'employee_type',
            'resignation_date', 'house_name', 'resumes', 'certificates', 'incentive', 'joining_bonus',
            'date_of_birth','pm_email',
            # ADD THE NEW FIELDS BELOW
            'pan_card', 'aadhaar', 'bank_name', 'bank_branch', 'bank_branch_address', 'bank_account', 'ifsc_code'
        ]


        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valid_to': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'resignation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Populate state queryset based on selected country in form data or instance
        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                self.fields['state'].queryset = state.objects.filter(country_id=country_id).order_by('name')
            except (ValueError, TypeError):
                self.fields['state'].queryset = state.objects.none()
        elif self.instance.pk and self.instance.country:
            self.fields['state'].queryset = state.objects.filter(country=self.instance.country).order_by('name')

        # Set resignation date required if employee_status is 'resigned'
        if self.instance and self.instance.employee_status == 'resigned':
            self.fields['resignation_date'].required = True
        else:
            self.fields['resignation_date'].required = False

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('employee_status')
        resignation_date = cleaned_data.get('resignation_date')

        if status == 'employed':
            cleaned_data['resignation_date'] = None
        elif status == 'resigned' and not resignation_date:
            raise ValidationError("Resignation date is required for resigned employees.")

        return cleaned_data

    def clean_resumes(self):
        return self._validate_files('resumes')

    def clean_certificates(self):
        return self._validate_files('certificates')

    def _validate_files(self, field_name):
        files = self.files.getlist(field_name)
        for file in files:
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ['.pdf', '.doc', '.docx']:
                raise ValidationError("Only PDF and DOC files are allowed.")
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise ValidationError("File must be under 5MB.")
        return files

    def clean_old_employee_id(self):
        value = self.cleaned_data.get("old_employee_id")
        if value in [None, '', 'None']:
            return None

        # Check if any other record already uses this old_employee_id
        qs = Employees.objects.filter(old_employee_id=value)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)  # exclude current record from check

        if qs.exists():
            raise forms.ValidationError("An employee with this Old Employee ID already exists.")

        return value

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle employee status and resignation date logic (already handled in cleaning)
        if instance.employee_status == 'employed':
            instance.resignation_date = None

        if commit:
            instance.save()
        return instance

        
from django import forms
from django.contrib.auth.models import User

class AdminRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user








class Holiday_Form(forms.Form):
    LEAVE_TYPE_CHOICES = [
        ('country', 'Country Holiday'),
        ('floating', 'Floating Holiday'),
        ('state', 'State Holiday'),
        
    ]

    leave_type = forms.ChoiceField(choices=LEAVE_TYPE_CHOICES, label="Leave Type", required=True)
    name = forms.CharField(max_length=100, label="Holiday Name", required=True)
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': None, 'max': None}),
        label="Holiday Date",
    )
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        empty_label="Select Country",
        label="Country"
    )
    

    state = forms.ModelChoiceField(
        queryset=state.objects.all(),  # Will be updated dynamically
        required=False,
        label="State"
    )




def clean_date(self):
    return self.cleaned_data['date']  # Accept any valid date without validation




# for passwrod change from the admin profile

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class AdminPasswordChangeForm(forms.ModelForm):
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        label="New Password",
        help_text="Your password must be at least 8 characters long and different from your current password."
    )
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm New Password")

    class Meta:
        model = User
        fields = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get the logged-in user
        super().__init__(*args, **kwargs)

    def clean_new_password(self):
        """Validate password strength and check if it's the same as the old password."""
        new_password = self.cleaned_data.get("new_password")

        # Apply Django's default password validators
        validate_password(new_password)

        # Check if new password is the same as the old password
        if self.user and self.user.check_password(new_password):
            raise forms.ValidationError("New password cannot be the same as the old password.")

        return new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data
