
from django import forms
from .models import Employees, Country, state
import random


STATUS_CHOICES = (
    ('employed', 'Employed'),
    ('resigned', 'Resigned'),
    ('maternal_leave', 'Maternal Leave'),
)

class EmployeeEditForm(forms.ModelForm):
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(), required=False, empty_label="Select a Country"
    )
    state = forms.ModelChoiceField(
        queryset=state.objects.none(), required=False, empty_label="Select a State"
    )
    employee_status = forms.ChoiceField(choices=STATUS_CHOICES, required=True)

    # Set non-mandatory fields
    emp_mname = forms.CharField(required=False)
    emp_off_ph = forms.CharField(required=False)
    emp_home_ph = forms.CharField(required=False)
    emp_resume = forms.FileField(required=False)
    emp_certif = forms.FileField(required=False)
    emp_cp_name = forms.CharField(required=False)

    employee_manager = forms.ModelChoiceField(
        queryset=Employees.objects.all(), required=False, empty_label="None"
    )

    employee_type = forms.ChoiceField(
        choices=Employees.EMPLOYEE_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Employees
        fields = [
            'emp_id', 'sal', 'emp_fname', 'emp_mname', 'emp_lname', 'emp_email', 'emp_pemail',
            'emp_mob_ph', 'emp_off_ph', 'emp_home_ph', 'emp_val_from', 'emp_val_to', 'country', 'state',
            'emp_home_street', 'emp_home_city', 'pincode', 'role', 'dep', 'designation',
            'employee_manager', 'employee_status', 'emp_cp_name', 'emp_cp_ph',
            'emp_cp_relation', 'emp_base', 'emp_resume', 'emp_certif','employee_type',

        ]
        widgets = {
            'emp_val_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'emp_val_to': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(EmployeeEditForm, self).__init__(*args, **kwargs)

        # Set country queryset
        self.fields['country'].queryset = Country.objects.all()

        # Ensure state queryset is properly set if country is selected
        if self.instance and self.instance.country:
            self.fields['state'].queryset = state.objects.filter(country=self.instance.country)
        else:
            self.fields['state'].queryset = state.objects.all()  # Show all states if no country is selected

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.employee_status = self.cleaned_data['employee_status']

        # Preserve existing salary value
        if 'emp_base' in self.cleaned_data:
            instance.emp_base = self.cleaned_data['emp_base']

        # Update emp_id prefix if employee_type changes
        if 'employee_type' in self.changed_data:  # Check if employee_type was changed
            new_type = self.cleaned_data['employee_type']
            if instance.emp_id:  # Extract numeric part from old ID
                existing_number = ''.join(filter(str.isdigit, instance.emp_id))
            else:
                existing_number = str(random.randint(1000, 9999))  # Generate a random number if missing

            instance.emp_id = f"{new_type}{existing_number}"  # Set new Employee ID

        if commit:
            instance.save()

        return instance






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
