#
# from django import forms
# from .models import Employees, Country, state
# import random
# from django.utils import timezone
#
#
# STATUS_CHOICES = (
#     ('employed', 'Employed'),
#     ('resigned', 'Resigned'),
#     ('maternal_leave', 'Maternal Leave'),
# )
#
# class EmployeeEditForm(forms.ModelForm):
#     country = forms.ModelChoiceField(
#         queryset=Country.objects.all(), required=False, empty_label="Select a Country"
#     )
#     state = forms.ModelChoiceField(
#         queryset=state.objects.none(), required=False, empty_label="Select a State"
#     )
#     employee_status = forms.ChoiceField(choices=STATUS_CHOICES, required=True)
#
#     # Set non-mandatory fields
#     emp_mname = forms.CharField(required=False)
#     emp_off_ph = forms.CharField(required=False)
#     emp_home_ph = forms.CharField(required=False)
#     emp_resume = forms.FileField(required=False)
#     emp_certif = forms.FileField(required=False)
#     emp_cp_name = forms.CharField(required=False)
#
#     employee_manager = forms.ModelChoiceField(
#         queryset=Employees.objects.all(), required=False, empty_label="None"
#     )
#
#     employee_type = forms.ChoiceField(
#         choices=Employees.EMPLOYEE_TYPE_CHOICES,
#         required=True,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#
#     resignation_date = forms.DateField(
#         required=False,
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#         label="Resignation Date"
#     )
#
#     class Meta:
#         model = Employees
#         fields = [
#             'emp_id', 'sal', 'emp_fname', 'emp_mname', 'emp_lname', 'emp_email', 'emp_pemail',
#             'emp_mob_ph', 'emp_off_ph', 'emp_home_ph', 'emp_val_from', 'emp_val_to', 'country', 'state',
#             'emp_home_street', 'emp_home_city', 'pincode', 'role', 'dep', 'designation',
#             'employee_manager', 'employee_status', 'emp_cp_name', 'emp_cp_ph',
#             'emp_cp_relation', 'emp_base', 'emp_resume', 'emp_certif','employee_type','resignation_date'  # Add this new field
#
#         ]
#         widgets = {
#             'emp_val_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'emp_val_to': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'resignation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
#         }
#
#     def __init__(self, *args, **kwargs):
#         super(EmployeeEditForm, self).__init__(*args, **kwargs)
#
#         # Conditional field requirement
#         if self.instance.employee_status == 'resigned':
#             self.fields['resignation_date'].required = True
#
#         # Set country queryset
#         self.fields['country'].queryset = Country.objects.all()
#
#         # Ensure state queryset is properly set if country is selected
#         if self.instance and self.instance.country:
#             self.fields['state'].queryset = state.objects.filter(country=self.instance.country)
#         else:
#             self.fields['state'].queryset = state.objects.all()  # Show all states if no country is selected
#
#     def save(self, commit=True):
#         instance = super().save(commit=False)
#         instance.employee_status = self.cleaned_data['employee_status']
#
#         # Preserve existing salary value
#         if 'emp_base' in self.cleaned_data:
#             instance.emp_base = self.cleaned_data['emp_base']
#
#         # Update emp_id prefix if employee_type changes
#         if 'employee_type' in self.changed_data:  # Check if employee_type was changed
#             new_type = self.cleaned_data['employee_type']
#             if instance.emp_id:  # Extract numeric part from old ID
#                 existing_number = ''.join(filter(str.isdigit, instance.emp_id))
#             else:
#                 existing_number = str(random.randint(1000, 9999))  # Generate a random number if missing
#
#             instance.emp_id = f"{new_type}{existing_number}"  # Set new Employee ID#
#
#
#
#             # Handle resignation date logic
#         if self.cleaned_data['employee_status'] == 'resigned':
#             # Set resignation date if either:
#             # 1. The field was manually filled, OR
#             # 2. No date exists yet
#             if 'resignation_date' in self.cleaned_data and self.cleaned_data['resignation_date']:
#                 instance.resignation_date = self.cleaned_data['resignation_date']
#             elif not instance.resignation_date:
#                 instance.resignation_date = timezone.now().date()  # Auto-set to today
#         else:
#             instance.resignation_date = None  # Clear if not resigned
#
#
#
#         if commit:
#             instance.save()
#
#         return instance


from django import forms
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.utils import timezone
import random
import os

from .models import Employees, Country, state, Salutation, Role, Department

STATUS_CHOICES = (
    ('employed', 'Employed'),
    ('resigned', 'Resigned'),
    ('maternal_leave', 'Maternal Leave'),
)


class EmployeeEditForm(forms.ModelForm):
    # Country and State Fields
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

    # Status Field
    employee_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=True
    )

    # Non-Mandatory Fields
    emp_mname = forms.CharField(required=False)
    emp_off_ph = forms.CharField(required=False)
    emp_home_ph = forms.CharField(required=False)
    emp_resume = forms.FileField(required=False)
    emp_certif = forms.FileField(required=False)
    # emp_cp_name = forms.CharField(required=False)

    # Employee Manager Field
    employee_manager = forms.ModelChoiceField(
        queryset=Employees.objects.all(),
        required=False,
        empty_label="None"
    )

    # Employee Type Field
    employee_type = forms.ChoiceField(
        choices=Employees.EMPLOYEE_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Resignation Date Field
    resignation_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Resignation Date"
    )

    class Meta:
        model = Employees
        fields = [
            'emp_id', 'sal', 'emp_fname', 'emp_mname', 'emp_lname',
            'emp_email', 'emp_pemail', 'emp_mob_ph', 'emp_off_ph',
            'emp_home_ph', 'emp_val_from', 'emp_val_to', 'country',
            'state', 'emp_home_street', 'emp_home_city', 'pincode',
            'dep', 'designation', 'employee_manager',
            'employee_status', 'emp_cp_name', 'emp_cp_ph',
            'emp_cp_relation', 'emp_base', 'emp_resume',
            'emp_certif', 'employee_type', 'resignation_date'
        ]

        widgets = {
            'emp_val_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'emp_val_to': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'resignation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        # Extract request from kwargs if passed
        self.request = kwargs.pop('request', None)

        super().__init__(*args, **kwargs)

        # Conditional field requirement
        if self.instance.employee_status == 'resigned':
            # Make resignation date optional
            self.fields['resignation_date'].required = False

        # Set country queryset
        self.fields['country'].queryset = Country.objects.all()

        # Ensure state queryset is properly set
        if self.instance and self.instance.country:
            self.fields['state'].queryset = state.objects.filter(country=self.instance.country)
        else:
            self.fields['state'].queryset = state.objects.all()

    def clean(self):
        """
        Validate and clean form data
        """
        cleaned_data = super().clean()

        # Validate employee status and resignation date
        employee_status = cleaned_data.get('employee_status')
        resignation_date = cleaned_data.get('resignation_date')

        # Handle status-specific logic
        if employee_status == 'employed':
            # Clear resignation date when status is employed
            cleaned_data['resignation_date'] = None
        elif employee_status == 'resigned':
            # Set resignation date if not provided
            if not resignation_date:
                cleaned_data['resignation_date'] = timezone.now().date()

        return cleaned_data

    def clean_emp_resume(self):
        """
        Validate resume file
        """
        resume = self.cleaned_data.get('emp_resume')
        if resume:
            try:
                # Get file extension
                file_ext = os.path.splitext(resume.name)[1].lower()

                # Allowed file extensions
                allowed_extensions = ['.pdf', '.doc', '.docx']

                # Check file extension
                if file_ext not in allowed_extensions:
                    raise ValidationError("Only PDF and DOC files are allowed.")

                # Check file size (5MB limit)
                if resume.size > 5 * 1024 * 1024:
                    raise ValidationError("Resume file must be less than 5MB.")

            except AttributeError:
                raise ValidationError("Invalid file format.")

        return resume

    def clean_emp_certif(self):
        """
        Validate certificate file
        """
        certif = self.cleaned_data.get('emp_certif')
        if certif:
            try:
                # Get file extension
                file_ext = os.path.splitext(certif.name)[1].lower()

                # Allowed file extensions
                allowed_extensions = ['.pdf', '.doc', '.docx']

                # Check file extension
                if file_ext not in allowed_extensions:
                    raise ValidationError("Only PDF and DOC files are allowed.")

                # Check file size (5MB limit)
                if certif.size > 5 * 1024 * 1024:
                    raise ValidationError("Certificate file must be less than 5MB.")

            except AttributeError:
                raise ValidationError("Invalid file format.")

        return certif

    def save(self, commit=True):
        """
        Custom save method with enhanced logic
        """
        try:
            # Create instance without saving
            instance = super().save(commit=False)

            # Update employee status
            instance.employee_status = self.cleaned_data['employee_status']

            # Preserve salary value
            if 'emp_base' in self.cleaned_data:
                instance.emp_base = self.cleaned_data['emp_base']

            # Update Employee ID if type changes
            if 'employee_type' in self.changed_data:
                new_type = self.cleaned_data['employee_type']
                existing_number = ''.join(filter(str.isdigit, instance.emp_id or '')) or \
                                  str(random.randint(1000, 9999))
                instance.emp_id = f"{new_type}{existing_number}"

            # Handle status-specific resignation date logic
            if instance.employee_status == 'employed':
                # Clear resignation date when status is employed
                instance.resignation_date = None
            elif instance.employee_status == 'resigned':
                # Set resignation date if not already set
                if not instance.resignation_date:
                    instance.resignation_date = timezone.now().date()

            # Handle file uploads
            if self.request and hasattr(self.request, 'FILES'):
                # Resume file handling
                resume_file = self.request.FILES.get('emp_resume')
                if resume_file:
                    try:
                        if instance.emp_resume:
                            default_storage.delete(instance.emp_resume.path)
                    except Exception as e:
                        print(f"Error deleting old resume: {e}")
                    instance.emp_resume = resume_file

                # Certificate file handling
                certif_file = self.request.FILES.get('emp_certif')
                if certif_file:
                    try:
                        if instance.emp_certif:
                            default_storage.delete(instance.emp_certif.path)
                    except Exception as e:
                        print(f"Error deleting old certificate: {e}")
                    instance.emp_certif = certif_file

            # Save the instance
            if commit:
                instance.save()

            return instance

        except Exception as e:
            # Comprehensive error logging
            print(f"Error in form save method: {e}")
            raise ValidationError(f"An error occurred while saving the form: {e}")







# forms.py
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





from django import forms

from django import forms


class Holiday_Form(forms.Form):
    LEAVE_TYPE_CHOICES = [
        ('fixed', 'Fixed Holiday'),
        ('floating', 'Floating Holiday'),
    ]

    leave_type = forms.ChoiceField(choices=LEAVE_TYPE_CHOICES, label="Leave Type")
    name = forms.CharField(max_length=100, label="Holiday Name")
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date',
            'min': None,  # Explicitly remove min
            'max': None,  }),
        label="Holiday Date",

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
