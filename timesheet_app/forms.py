

from django.db.models import Q
from django import forms
from admin_app.models import Client, Project,Employees,AssignProject,Country,CostCenter

class ClientForm(forms.ModelForm):
    """
    Form for creating or updating a Client.
    Ensures alias is uppercase and all fields are required.
    Adds 'is_active' checkbox only when editing.
    """

    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        empty_label="Select Country",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Client
        fields = ['client_name', 'client_alias', 'client_addr', 'country']
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name'
            }),
            'client_alias': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Short Alias'
            }),
            'client_addr': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Address'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add is_active only if editing existing client
        if self.instance and self.instance.pk:
            self.fields['is_active'] = forms.BooleanField(
                required=False,
                initial=self.instance.is_active,
                label="Active",
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
            )

    def clean_client_alias(self):
        alias = self.cleaned_data.get('client_alias')
        return alias.upper() if alias else alias

class ProjectForm(forms.ModelForm):
    """
    Form for creating or updating a Project.
    Includes validation for date fields and user-friendly widgets.
    """
    
    class Meta:
        model = Project
        fields = [
            'project_name', 
            'valid_from', 
            'valid_to', 
            'client', 
            'project_desc', 
            'prj_manager', 
            'is_active'
        ]
        widgets = {
            'project_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Project Name'
            }),
            'valid_from': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'valid_to': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'client': forms.Select(attrs={
                'class': 'form-control'
            }),
            'project_desc': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter Short Project Description'
            }),
            'prj_manager': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Show full name of employee in dropdown
        self.fields['prj_manager'].queryset = Employees.objects.all()

        self.fields['prj_manager'].label_from_instance = lambda obj: (
            f"{obj.employee_id} - {obj.first_name} {obj.last_name}"
        )

        # Optional: Set default value or initial UI behavior
        self.fields['project_name'].widget.attrs['autofocus'] = True

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        
        # Check that valid_to is not before valid_from
        # This check is performed only if both dates are provided
        if valid_from and valid_to:
            if valid_to < valid_from:
                # Add a field-specific error
                self.add_error('valid_to', "End date cannot be before start date.")

        return cleaned_data



# assign_project/forms.py
from django import forms
from django.forms import DateInput



class BaseAssignProjectForm(forms.ModelForm):
    employee = forms.ModelChoiceField(
        queryset=Employees.objects.all().order_by('employee_id'),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label="Employee"
    )
    client = forms.ModelChoiceField(
        queryset=Client.objects.all().only("client_id", "client_name").order_by('client_name'),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        required=True,
        label="Client"
    )

    class Meta:
        model = AssignProject
        fields = ['client', 'project', 'employee', 'designation', 'start_date', 'end_date']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'designation': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'start_date': DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'end_date': DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.none()
        self.fields['employee'].label_from_instance = lambda emp: f"{emp.employee_id} - {emp.first_name} {emp.last_name}"

        if 'client' in self.data:
            try:
                client_id = int(self.data.get('client'))
                self.fields['project'].queryset = Project.objects.filter(
                    client_id=client_id, is_active=True
                ).only("project_id", "project_name").order_by('project_name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.project:
            self.fields['project'].queryset = Project.objects.filter(
                client=self.instance.project.client, is_active=True
            ).only("project_id", "project_name").order_by('project_name')
            self.fields['client'].initial = self.instance.project.client

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        employee = cleaned_data.get('employee')

        # 0. Ensure start_date is set.
        if not start_date:
            self.add_error('start_date', 'Start date is required.')

        # 1. Enforce that an end_date is required if a start_date is provided
        if start_date and not end_date:
            self.add_error('end_date', "An end date is required when a start date is set.")

        # 2. End date cannot be before the start date (only run if both dates exist)
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', "End date cannot be before start date.")

        # 3. Within project validity (only run if both dates and project exist)
        if project and start_date and end_date:
            if start_date < project.valid_from:
                self.add_error('start_date', f"Start date cannot be before project validity ({project.valid_from}).")
            if end_date > project.valid_to:
                self.add_error('end_date', f"End date cannot be after project validity ({project.valid_to}).")

        # 4. Overlapping assignments (only run if all fields exist)
        if employee and project and start_date and end_date:
            qs = AssignProject.objects.filter(employee=employee, project=project).exclude(pk=self.instance.pk)
            qs = qs.filter(start_date__lte=end_date).filter(Q(end_date__isnull=True) | Q(end_date__gte=start_date))
            if qs.exists():
                raise forms.ValidationError(
                    "This employee is already assigned to this project in the selected date range."
                )

        return cleaned_data
class AssignProjectCreateForm(BaseAssignProjectForm):
    pass


class AssignProjectUpdateForm(BaseAssignProjectForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set client as initial value if instance exists
        if self.instance.pk:
            self.fields['client'].initial = self.instance.project.client


class CostCenterForm(forms.ModelForm):
    class Meta:
        model = CostCenter
        fields = ['costcenter_name', 'is_active']
        widgets = {
            'costcenter_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }