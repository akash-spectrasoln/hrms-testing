

from django.db.models import Q
from django import forms
from admin_app.models import Client, Project,Employees,AssignProject,Country,CostCenter

class ClientForm(forms.ModelForm):
    """
    Form for creating or updating a Client.
    Ensures alias is uppercase and all fields are required.
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
# assign_project/forms.py
from django import forms
from django.forms import DateInput



class BaseAssignProjectForm(forms.ModelForm):
    # Define the employee field with the sorted queryset here
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

        # Dynamic project filtering
        self.fields['project'].queryset = Project.objects.none()

        # Label formatting
        self.fields['employee'].label_from_instance = lambda emp: f"{emp.employee_id} - {emp.first_name} {emp.last_name}"

        if 'client' in self.data:
            try:
                client_id = int(self.data.get('client'))
                self.fields['project'].queryset = Project.objects.filter(
                    client_id=client_id, is_active=True
                ).only("project_id", "project_name", "client").order_by('project_name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.project:
            self.fields['project'].queryset = Project.objects.filter(
                client=self.instance.project.client, is_active=True
            ).only("project_id", "project_name", "client").order_by('project_name')

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if not start_date:
            raise forms.ValidationError("Start Date is required.")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        if not end_date:
            raise forms.ValidationError("End Date is required.")
        return end_date


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