# employee_app/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Employees

# forms.py
from django import forms
#
# class LoginForm(forms.Form):
#     emp_email = forms.EmailField(label="Email", max_length=100)
#     password = forms.CharField(label="Password", widget=forms.PasswordInput)
#     confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)




# forms.py (in employee_app)

from django import forms
from .models import Employees, Country, state

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

    class Meta:
        model = Employees
        fields = [
            'first_name', 'middle_name', 'last_name', 'personal_email', 'mobile_phone',
            'home_phone', 'address', 'home_city', 'country', 'state',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_email',
            'emergency_contact_relation'
        ]

    # Override the middle_name field to make it not required
    middle_name = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize state field based on the selected country
        if self.instance and self.instance.country:
            self.fields['state'].queryset = state.objects.filter(country=self.instance.country)
        else:
            self.fields['state'].queryset = state.objects.none()

        # Additional initialization logic if needed

from django import forms
from django.contrib.auth.forms import PasswordChangeForm


# from django.contrib.auth.forms import PasswordChangeForm
# from django.core.exceptions import ValidationError
#
# class CustomPasswordChangeForm(PasswordChangeForm):
#     def clean_new_password2(self):
#         new_password = self.cleaned_data.get("new_password2")
#         old_password = self.cleaned_data.get("old_password")
#
#         if old_password and new_password and old_password == new_password:
#             raise ValidationError("The new password cannot be the same as the old password.")
#
#         return new_password





from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

class CustomPasswordChangeForm(PasswordChangeForm):
    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")
        old_password = self.cleaned_data.get("old_password")

        # Check if old password and new password are the same
        if old_password and new_password1 and old_password == new_password1:
            raise ValidationError("The new password cannot be the same as the old password.")

        # Check if new password1 and new password2 match
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise ValidationError("The new password and confirm password must match.")

        # **Check password strength using Django's built-in validators**
        validate_password(new_password1, self.user)

        return new_password2




# employee_app/forms.py
# from django import forms
# from .models import LeaveRequest
# from .models import Holiday
#
# class LeaveRequestForm(forms.ModelForm):
#     class Meta:
#         model = LeaveRequest
#         fields = ['start_date', 'end_date', 'reason']
#         widgets = {
#             'start_date': forms.DateInput(attrs={'type': 'date'}),
#             'end_date': forms.DateInput(attrs={'type': 'date'}),
#             'reason': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
#         }
#
#     def clean(self):
#         cleaned_data = super().clean()
#         start_date = cleaned_data.get('start_date')
#         end_date = cleaned_data.get('end_date')
#
#         # Fetch all holidays
#         holidays = Holiday.objects.values_list('date', flat=True)
#
#         # Check if the selected start date is a holiday
#         if start_date in holidays:
#             self.add_error('start_date', 'The selected start date is a holiday.')
#
#         # Check if the selected end date is a holiday
#         if end_date in holidays:
#             self.add_error('end_date', 'The selected end date is a holiday.')
#
#         # Check that start_date is before end_date
#         if start_date and end_date and start_date > end_date:
#             self.add_error('end_date', 'End date must be after start date.')
#
#         return cleaned_data



#
from django import forms
from .models import LeaveRequest

# class LeaveRequestForm(forms.ModelForm):
#     class Meta:
#         model = LeaveRequest
#         fields = ['start_date', 'end_date', 'reason']  # Exclude employee_master
#         widgets = {
#             'start_date': forms.DateInput(attrs={'type': 'date'}),
#             'end_date': forms.DateInput(attrs={'type': 'date'}),
#             'reason': forms.Textarea(attrs={'rows': 4}),
#         }
#
#     def _init_(self, *args, **kwargs):
#         user = kwargs.pop('user', None)  # Accept user parameter
#         super().__init__(*args, **kwargs)



# from django import forms
# from .models import LeaveRequest
#
# class LeaveRequestForm(forms.ModelForm):
#     class Meta:
#         model = LeaveRequest
#         fields = ['leave_type','start_date', 'end_date', 'reason']  # Exclude employee_master
#         widgets = {
#             'start_date': forms.DateInput(attrs={'type': 'date'}),
#             'end_date': forms.DateInput(attrs={'type': 'date'}),
#             'reason': forms.Textarea(attrs={'rows': 4}),
#         }
#
#     def __init__(self, *args, **kwargs):  # Fixed method name (double underscores)
#         self.user = kwargs.pop('user', None)  # Accept and remove 'user' parameter
#         super().__init__(*args, **kwargs)  # Call the parent __init__
#
#         # Example: Add custom logic if needed based on the user
#         if self.user:
#             # You can filter fields or add specific logic here
#             pass




from django import forms
from .models import LeaveRequest

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Allow "one-day leave" if end_date not filled: auto-copy start_date.
        if start_date and not end_date:
            cleaned_data['end_date'] = start_date
            end_date = start_date

        # Validate that end_date is not earlier than start_date
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be before the start date.")

        return cleaned_data
