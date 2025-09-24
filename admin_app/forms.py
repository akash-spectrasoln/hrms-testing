from django import forms
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.utils import timezone
import random
import os
import logging
from .models import Employees, Country, state, Salutation, Role, Department,Resume,Certificate,CostCenter, DeviceTracker
from django.db import models

logger = logging.getLogger(__name__)

import os
from django import forms
from django.core.exceptions import ValidationError
from .models import Employees, Resume, Certificate, Country, state,DeviceTracker,Devices

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
    cost_center = forms.ModelChoiceField(
    queryset=CostCenter.objects.all(),
    )
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
            'department', 'role', 'manager','cost_center','home_city','pincode','emergency_contact_name','emergency_contact_phone','emergency_contact_email',
             'emergency_contact_relation',
             'base_salary','employee_type','employee_status',
            'resignation_date', 'house_name', 'resumes', 'certificates', 'incentive', 'joining_bonus',
            'date_of_birth','pm_email',
            # ADD THE NEW FIELDS BELOW
            'pan_card', 'aadhaar', 'bank_name', 'bank_branch', 'bank_branch_address', 'bank_account', 'ifsc_code','hr_emails'
        ]


        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valid_to': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'resignation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        editing = kwargs.pop('editing', False)
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

        # Check if we're updating (instance exists and has a primary key)
        if self.instance and self.instance.pk:
            self.fields['employee_status'].required = True  # Required during update
        else:
            self.fields['employee_status'].required = False 

        if editing:
            # Remove employee_type field only in update mode
            self.fields.pop('employee_type', None)

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
    

from django import forms
from .models import SetUpTable

class SetUpTableForm(forms.ModelForm):
    class Meta:
        model = SetUpTable
        fields = ['field', 'value']
        widgets = {
            'field': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'value': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Devices
        fields = [
            "device_model", "device_type", "device_brand", "serial_no",
            "proc_date", "retire_date", "price", "active"
        ]
        widgets = {
            "device_model": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "device_type": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "device_brand": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "serial_no": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "proc_date": forms.DateInput(attrs={"type": "date", "class": "form-control form-control-sm"}),
            "retire_date": forms.DateInput(attrs={"type": "date", "class": "form-control form-control-sm"}),
            "price": forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # New instance
            self.fields['active'].initial = True

    def clean(self):
        cleaned_data = super().clean()
        proc_date = cleaned_data.get("proc_date")
        retire_date = cleaned_data.get("retire_date")

        if proc_date and retire_date and retire_date < proc_date:
            self.add_error("retire_date", "Retire date cannot be before procurement date.")

        return cleaned_data

from django import forms
from .models import DeviceTracker, Devices, Employees
from django.db.models import Q
class DeviceTrackerForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control form-control-sm"})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control form-control-sm"})
    )

    class Meta:
        model = DeviceTracker
        fields = ["employee", "device", "start_date", "end_date"]
        widgets = {
            "employee": forms.Select(attrs={"class": "form-control form-control-sm employee-select2"}),
            "device": forms.Select(attrs={"class": "form-control form-control-sm device-select2"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make device field not required initially to handle AJAX submissions
        self.fields['device'].required = False

        # Employee dropdown
        self.fields["employee"].queryset = Employees.objects.all().order_by("employee_id")
        self.fields["employee"].label_from_instance = (
            lambda obj: f"{obj.employee_id} - {obj.first_name} {obj.last_name}"
        )

        # Base queryset for available devices
        available_devices = Devices.objects.filter(
            active=True, retire_date__isnull=True
        ).exclude(
            device_trackers__end_date__isnull=True  # Exclude actively assigned devices
        )
        
        print(f"[DEBUG] Base available devices query: {available_devices.query}")

        print(f"[DEBUG] Available devices before filters: {list(available_devices)}")

        # Include current device in edit mode
        if self.instance.pk and self.instance.device:
            available_devices = available_devices | Devices.objects.filter(pk=self.instance.device.pk)
            print(f"[DEBUG] Available devices in edit mode (current device included): {list(available_devices)}")

        # Include selected device in create mode if posted
        if self.data and self.data.get("device"):
            try:
                device_id = int(self.data.get("device"))
                available_devices = available_devices | Devices.objects.filter(pk=device_id)
                print(f"[DEBUG] Available devices in create mode (selected device included): {list(available_devices)}")
            except (TypeError, ValueError):
                print(f"[DEBUG] Invalid device ID in POST: {self.data.get('device')}")

        print(f"[DEBUG] Final available devices after queryset filtering: {list(available_devices)}")

        # Assign final queryset and label formatting
        self.fields["device"].queryset = available_devices.distinct().order_by(
            "device_brand__device_brand",
            "device_type__device_type",
            "device_model"
        )
        self.fields["device"].label_from_instance = (
            lambda obj: f"{self._get_device_icon(obj.device_type.device_type)} {obj.device_brand.device_brand} {obj.device_model} - {obj.serial_no}"
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        device = cleaned_data.get("device")
        
        # Debugging lines to check raw POST data and form state
        print(f"[DEBUG] Raw POST data for device: {self.data.get('device') if self.data else 'No data'}")
        print(f"[DEBUG] Form data keys: {list(self.data.keys()) if self.data else 'No data'}")
        print(f"[DEBUG] Device field errors: {self.errors.get('device', [])}")
        print(f"[DEBUG] All form errors: {self.errors}")
        print(f"[DEBUG] Cleaning form: device={device}, start_date={start_date}, end_date={end_date}")

        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date cannot be before start date.")

        if device and start_date:
            end_compare = end_date or start_date

            overlaps = DeviceTracker.objects.filter(device=device).exclude(pk=self.instance.pk).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=start_date),
                start_date__lte=end_compare
            )
            print(f"[DEBUG] Overlaps found for device {device}: {overlaps.exists()}")

            if overlaps.exists() and (not self.instance.pk or self.instance.device != device):
                print(f"[DEBUG] Overlap detected for device: {device}. Adding error.")
                self.add_error("device", "This device is already assigned during the selected period.")

        return cleaned_data

    def clean_device(self):
        """Custom validation for device field to handle Select2 AJAX submissions."""
        device = self.cleaned_data.get('device')
        
        print(f"[DEBUG] clean_device called with device: {device}")
        print(f"[DEBUG] device type: {type(device)}")
        
        # If device is already a Devices instance, return it
        if isinstance(device, Devices):
            print(f"[DEBUG] Device is already a Devices instance: {device}")
            return device
            
        # If device is None or empty, check if it was provided in POST data
        if not device and self.data and self.data.get('device'):
            try:
                device_id = int(self.data.get('device'))
                device = Devices.objects.get(pk=device_id)
                print(f"[DEBUG] Retrieved device from POST data: {device}")
                return device
            except (ValueError, TypeError, Devices.DoesNotExist) as e:
                print(f"[DEBUG] Error retrieving device from POST data: {e}")
                raise forms.ValidationError("Please select a valid device.")
        
        # If device is still None, raise validation error
        if not device:
            raise forms.ValidationError("This field is required.")
            
        return device

    def full_clean(self):
        """Override full_clean to handle device field validation properly."""
        # First, try to fix the device field before calling super().full_clean()
        if self.data and self.data.get('device') and not hasattr(self, 'cleaned_data'):
            try:
                device_id = int(self.data.get('device'))
                device = Devices.objects.get(pk=device_id)
                print(f"[DEBUG] Pre-fixing device from POST data: {device}")
                # Set the device in the form data to ensure it's included in validation
                self.data = self.data.copy()
                self.data['device'] = device_id
            except (ValueError, TypeError, Devices.DoesNotExist) as e:
                print(f"[DEBUG] Could not pre-fix device from POST data: {e}")
                pass
        
        super().full_clean()
        
        # If device field still has errors and we have device data in POST, try to fix it
        if 'device' in self.errors and self.data and self.data.get('device'):
            try:
                device_id = int(self.data.get('device'))
                device = Devices.objects.get(pk=device_id)
                print(f"[DEBUG] Post-fixing device from POST data: {device}")
                # Clear the error and set the cleaned data
                if 'device' in self.errors:
                    del self.errors['device']
                self.cleaned_data['device'] = device
            except (ValueError, TypeError, Devices.DoesNotExist) as e:
                print(f"[DEBUG] Could not post-fix device from POST data: {e}")
                pass

    def save(self, commit=True):
        """Override save method to ensure device is properly set."""
        instance = super().save(commit=False)
        
        # Ensure device is set from cleaned_data
        if 'device' in self.cleaned_data and self.cleaned_data['device']:
            instance.device = self.cleaned_data['device']
            print(f"[DEBUG] Set device in save method: {instance.device}")
        
        if commit:
            instance.save()
            print(f"[DEBUG] Saved instance with device: {instance.device}")
        
        return instance

    def _get_device_icon(self, device_type):
        """Get appropriate icon for device type."""
        icon_map = {
            'laptop': '💻',
            'mouse': '🖱️',
            'keyboard': '⌨️',
            'monitor': '🖥️',
            'desktop': '🖥️',
            'tablet': '📱',
            'phone': '📱',
            'printer': '🖨️',
            'scanner': '📄',
            'headphone': '🎧',
            'speaker': '🔊',
            'camera': '📷',
            'projector': '📽️',
            'computer': '💻',
            'pc': '🖥️',
        }
        
        # Get the icon for the device type (case insensitive)
        device_type_lower = device_type.lower() if device_type else ''
        for key, icon in icon_map.items():
            if key in device_type_lower:
                return icon
        
        # Default icon for unknown types
        return '🔧'
