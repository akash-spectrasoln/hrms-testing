
from django.shortcuts import render
from django.http import HttpResponse
from.models import *

#
# from django.shortcuts import render
from django.http import HttpResponse
from .models import Role, state, Country ,Employees,Department
from datetime import datetime,date



#
# index page view

def index(request):
    return render(request,'index.html')



def admin_index(request):
    return render(request,'admin_index.html')

# adding employees view


from django.contrib import messages

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import Employees, Salutation, Country, state, Department, Role
from .forms import EmployeeEditForm
from datetime import date, datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import date

from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import date
from .forms import EmployeeEditForm
from .models import Role, Department, state, Country, Salutation, Employees

def add_employee(request):
    if request.method == 'POST':
        form = EmployeeEditForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            try:
                employee = form.save(commit=False)  # Save the form but don't commit to the database yet
                employee.save()  # Now save the employee instance
                
                # Handle Admin Privileges
                is_admin = request.POST.get('is_admin') == 'on'  # Fetch and check the 'is_admin' checkbox
                print(is_admin)
                # Ensure the employee has an associated user object
                if employee.user:
                    user_obj = employee.user
                    user_obj.is_superuser = is_admin  # Set admin privileges as per checkbox state
                    user_obj.is_staff = is_admin      # Typically set is_staff alongside is_superuser
                    user_obj.save()

                # Handle multiple resumes
                for resume_file in request.FILES.getlist('resumes'):
                    Resume.objects.create(employee=employee, file=resume_file)

                # Handle multiple certificates
                for certificate_file in request.FILES.getlist('certificates'):
                    Certificate.objects.create(employee=employee, file=certificate_file)

                messages.success(request, "Employee added successfully!")
                return redirect('add_employee')
            except Exception as e:
                messages.error(request, f"An error occurred while saving: {e}")
        else:
            # Print form errors in console for debugging
            print("Form Errors:", form.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeEditForm(request=request)

    # Fetch dropdown and default data
    context = {
        'form': form,
        'roles': Role.objects.all(),
        'departments': Department.objects.all(),
        'states': state.objects.all(),
        'countries': Country.objects.all(),
        'salutations': Salutation.objects.all(),
        'employees': Employees.objects.all(),
        'default_valid_from': date.today(),
        'default_valid_to': date(9999, 12, 31),
    }
    return render(request, 'add_employee.html', context)



from django.http import JsonResponse
from .models import state  # Keep 'state' lowercase, as defined in your model

def get_states(request):
    country_id = request.GET.get('country_id')  # Get country ID from the request
    if country_id:
        states = state.objects.filter(country_id=country_id).values('id', 'name')  # Use 'state' lowercase
        print(states)  # Debugging line
        return JsonResponse(list(states), safe=False)  # Return states as JSON
    return JsonResponse({'error': 'Country not selected'}, status=400)







import openpyxl
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from .models import Employees

def export_employees_to_excel(request):
    # Create a workbook and add a worksheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Employees'

    # Define the header row
    headers = [
        'Employee ID', 'Salutation', 'First Name', 'Middle Name', 'Last Name',
        'Company Email', 'Personal Email', 'Mobile Phone', 'Office Phone', 'Home Phone',
        'Valid From', 'Valid To', 'Country', 'State', 'Address', 'Home House',
        'Home City', 'Pincode', 'Role', 'Department', 'Designation', 'Manager',
        'Employee Status', 'Emergency Contact Name', 'Emergency Contact Phone',
        'Emergency Contact Email', 'Emergency Contact Relation', 'Base Salary',
        'Resume', 'Certificates', 'Created On', 'Modified On', 'Is Deleted',
        'Floating Holidays Balance', 'Floating Holidays Used', 'Total Leaves',
        'Used Leaves'
    ]

    # Write the header row to the sheet
    for col_num, header in enumerate(headers, 1):
        col_letter = get_column_letter(col_num)
        sheet[f'{col_letter}1'] = header

    # Query all employees
    employees = Employees.objects.select_related('salutation', 'country', 'state', 'role', 'department', 'manager')

    # Write employee data to the sheet
    for row_num, employee in enumerate(employees, 2):
        # Convert datetime fields to naive datetime
        created_on = employee.created_on.replace(tzinfo=None) if employee.created_on else ''
        modified_on = employee.modified_on.replace(tzinfo=None) if employee.modified_on else ''

        row = [
            employee.employee_id,
            employee.salutation.sal_name if employee.salutation else '',
            employee.first_name,
            employee.middle_name,
            employee.last_name,
            employee.company_email,
            employee.personal_email,
            employee.mobile_phone,
            employee.office_phone,
            employee.home_phone,
            employee.valid_from,
            employee.valid_to,
            employee.country.country_name if employee.country else '',
            employee.state.name if employee.state else '',
            employee.address,
            employee.home_house,
            employee.home_city,
            employee.pincode,
            employee.role.role_name if employee.role else '',
            employee.department.dep_name if employee.department else '',
            employee.designation,
            f"{employee.manager.first_name} {employee.manager.last_name}" if employee.manager else '',
            employee.employee_status,
            employee.emergency_contact_name,
            employee.emergency_contact_phone,
            employee.emergency_contact_email,
            employee.emergency_contact_relation,
            float(employee.base_salary),
            
            created_on,
            modified_on,
            employee.is_deleted,
            employee.floating_holidays_balance,
            employee.floating_holidays_used,
            employee.total_leaves,
            employee.used_leaves
        ]

        for col_num, cell_value in enumerate(row, 1):
            col_letter = get_column_letter(col_num)
            sheet[f'{col_letter}{row_num}'] = cell_value

    # Set the response headers
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=employees.xlsx'

    # Save the workbook to the response
    workbook.save(response)

    return response






from django.db.models import Q
from django.utils import timezone



from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone
from .models import Employees

def list_employees(request):
    # Start with base queryset
    queryset = Employees.objects.filter(is_deleted=False)

    # Get filter parameters
    emp_id = request.GET.get('employee_id', '').strip()
    name = request.GET.get('name', '').strip()
    status = request.GET.get('employee_status', 'employed')  # Default to employed
    print(emp_id)
    print(name)
    # Apply status filter
    if status != 'all':
        queryset = queryset.filter(employee_status=status)

    # Apply other filters
    if emp_id:
        queryset = queryset.filter(employee_id__icontains=emp_id)
    if name:
        queryset = queryset.filter(
            Q(first_name__icontains=name) |
            Q(last_name__icontains=name)
        )

    # Prepare employee data
    today = timezone.now().date()
    employee_list = []

    for employee in queryset.select_related('manager', 'department'):
        # Skip if no primary key
        if not employee.pk:
            continue

        # Manager info
        manager_display = (
            f"{employee.manager.employee_id} ({employee.manager.first_name})"
            if employee.manager else "None"
        )

        # Resignation info
        resignation_tooltip = ""
        if employee.employee_status == 'resigned' and employee.resignation_date:
            formatted_date = employee.resignation_date.strftime('%b %d, %Y')
            days_ago = (today - employee.resignation_date).days
            resignation_tooltip = f"Resigned on {formatted_date} ({days_ago} days ago)"

        employee_list.append({
            'pk': employee.pk,
            'employee_id': employee.employee_id,
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'company_email': employee.company_email,
            'mobile_phone': employee.mobile_phone,
            'department': employee.department.dep_name if employee.department else "",
            'designation': employee.designation,
            'employee_status': employee.employee_status,
            'manager_display': manager_display,
            'resignation_tooltip': resignation_tooltip,
            'resignation_date': employee.resignation_date,
            'today': date.today(),
        })

    context = {
        'employee_list': employee_list,
        'current_filters': {
            'emp_id': emp_id,
            'name': name,
            'status': status
        }
    }

    return render(request, 'list_employees.html', context)




from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from datetime import date
from .models import LeaveRequest, Employees  # Adjust this import if your app name/model name differs

def delete_leave_request(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    employee = leave.employee_user
    leave_days = leave.leave_days  # Ensure this exists in your model
    current_user = Employees.objects.get(user=request.user)

    try:
        emp_obj = Employees.objects.get(company_email=employee.email)
    except Employees.DoesNotExist:
        emp_obj = None

    if emp_obj:
        if leave.leave_type == "Casual Leave":
            emp_obj.used_leaves = max(emp_obj.used_leaves - leave_days, 0)
            emp_obj.save()
        elif leave.leave_type == "Floating Leave":
            emp_obj.floating_holidays_used = max(emp_obj.floating_holidays_used - leave_days, 0)
            emp_obj.save()
        # ...handle other leave types as needed

    # Soft delete instead of hard delete
    leave.status='Deleted'
    leave.approved_by=current_user.user
    leave.save()
    messages.success(request, "Leave request deleted successfully.")

    return redirect("leave_request_display")







from django.views.generic import UpdateView
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Employees, Country, state
from .forms import EmployeeEditForm




from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.files.storage import default_storage
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

# Import models
from .models import (
    Employees, Salutation, Role, Department,
    Country, state
)
from .forms import EmployeeEditForm

import logging
import traceback

# Configure logging
logger = logging.getLogger(__name__)


from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.core.files.storage import default_storage
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging
import traceback
from .models import Employees, Salutation, Country, state, Department, Role
from .forms import EmployeeEditForm



logger = logging.getLogger(__name__)

class EmployeeUpdateView(UpdateView):
    model = Employees
    form_class = EmployeeEditForm
    template_name = 'employeeupdate.html'
    success_url = reverse_lazy('employee_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context['salutations'] = Salutation.objects.all()
            context['roles'] = Role.objects.all()
            context['departments'] = Department.objects.all()
            context['managers'] = Employees.objects.filter(employees_managed__isnull=False).distinct()
            context['employees'] = Employees.objects.all()
            employee = self.object
            context['countries'] = Country.objects.all()
            context['selected_country'] = employee.country if employee.country else None
            context['states'] = state.objects.filter(country=employee.country) if employee.country else []
            context['selected_state'] = employee.state if employee.state else None
            context['home_post_office'] = employee.home_post_office
            context['incentive'] = employee.incentive
            return context
        except Exception as e:
            logger.error(f"Error in get_context_data: {str(e)}")
            logger.error(traceback.format_exc())
            messages.error(self.request, f"An error occurred while preparing the form: {str(e)}")
            raise

    @transaction.atomic
    def form_valid(self, form):
        try:
            employee = form.save(commit=False)
            current_status = form.cleaned_data.get('employee_status')
            new_employee_type = form.cleaned_data.get("employee_type")

            if current_status == 'employed':
                employee.resignation_date = None
            elif current_status == 'resigned' and not employee.resignation_date:
                employee.resignation_date = timezone.now().date()

            if new_employee_type and new_employee_type != employee.employee_type:
                unique_number = employee.employee_id[-4:]
                employee.employee_id = f"{new_employee_type}{unique_number}"

            if 'delete_resumes' in self.request.POST:
                for resume_id in self.request.POST.getlist('delete_resumes'):
                    try:
                        resume = Resume.objects.get(id=resume_id, employee=employee)
                        resume.file.delete()
                        resume.delete()
                    except Resume.DoesNotExist:
                        continue

            if 'delete_certificates' in self.request.POST:
                for certificate_id in self.request.POST.getlist('delete_certificates'):
                    try:
                        certificate = Certificate.objects.get(id=certificate_id, employee=employee)
                        certificate.file.delete()
                        certificate.delete()
                    except Certificate.DoesNotExist:
                        continue

            if self.request.FILES.getlist('resumes'):
                for resume_file in self.request.FILES.getlist('resumes'):
                    Resume.objects.create(employee=employee, file=resume_file)

            if self.request.FILES.getlist('certificates'):
                for certificate_file in self.request.FILES.getlist('certificates'):
                    Certificate.objects.create(employee=employee, file=certificate_file)

            employee.save()

            # -------- ADMIN PRIVILEGE HANDLING --------
            is_admin = self.request.POST.get('is_admin') == 'on'
            print("admin or not",is_admin)
            if hasattr(employee, 'user') and employee.user is not None:
                user_obj = employee.user
                user_obj.is_superuser = is_admin
                user_obj.is_staff = is_admin
                user_obj.save()
            # ------------------------------------------

            messages.success(self.request, "✅ Employee details updated successfully.")
            return super().form_valid(form)

        except ValidationError as ve:
            messages.error(self.request, f"Validation Error: {str(ve)}")
            return self.form_invalid(form)

        except Exception as e:
            logger.error(f"Unexpected error in form_valid: {str(e)}")
            logger.error(traceback.format_exc())
            transaction.set_rollback(True)
            messages.error(self.request, f"An unexpected error occurred: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.error("Form Validation Failed")
        logger.error("Form Errors: %s", form.errors)
        logger.error("POST Data: %s", self.request.POST)

        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f"Error in {field}: {error}")

        messages.error(self.request, "There was an error updating the employee details. Please check the form.")
        return super().form_invalid(form)
    
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
import pandas as pd
from .models import Employees, Country, state, Role, Department, Salutation

class EmployeeExcelCreateView(View):
    template_name = 'employee_excel_create.html'

    def get(self, request):
        print("GET request received")
        return render(request, self.template_name)

    def post(self, request):
        print("POST request received")
        excel_file = request.FILES.get('excel_file')

        if not excel_file:
            print("No file uploaded")
            return JsonResponse({'error': "Please upload an Excel file."}, status=400)

        created_employees = []  # List to store successfully created employees

        try:
            df = pd.read_excel(excel_file)
            print("DataFrame loaded successfully")
            print(df.head())  # Print the first few rows of the DataFrame for inspection

            for index, row in df.iterrows():
                print(f"Processing row {index + 1}")
                try:
                    # Fetch foreign key objects
                    country = Country.objects.get(country_name=row['Country'])
                    print(f"Country found: {country}")
                    state_obj = state.objects.get(name=row['State'], country=country)
                    print(f"State found: {state_obj}")
                    role = Role.objects.get(role_name=row['Role'])
                    print(f"Role found: {role}")
                    department = Department.objects.get(dep_name=row['Department'])
                    print(f"Department found: {department}")
                    salutation = Salutation.objects.get(sal_name=row.get('Salutation', 'Mr.'))
                    print(f"Salutation found: {salutation}")
                    manager_id = Employees.objects.get(employee_id=row['Manager ID'])
                    print(f"Manager found: {manager_id}")

                    # Create a new employee
                    employee = Employees(
                        employee_id=row['Employee ID'],
                        first_name=row['First Name'],
                        middle_name=row.get('Middle Name', ''),
                        last_name=row['Last Name'],
                        company_email=row['Company Email'],
                        personal_email=row.get('Personal Email', ''),
                        mobile_phone=row['Mobile Phone'],
                        office_phone=row.get('Office Phone', ''),
                        home_phone=row.get('Home Phone', ''),
                        home_city=row.get('Home City', ''),
                        home_post_office=row.get('Home Post Office', ''),
                        home_house=row.get('Home House', ''),
                        pincode=row.get('Pincode', ''),
                        department=department,
                        designation=row.get('Designation', ''),
                        manager=manager_id,
                        employee_status=row['Employee Status'],
                        emergency_contact_name=row.get('Emergency Contact Name', ''),
                        emergency_contact_phone=row.get('Emergency Contact Phone', ''),
                        emergency_contact_relation=row.get('Emergency Contact Relation', ''),
                        base_salary=row.get('Base Salary', 0),
                        incentive=row.get('incentive',0.0),
                        employee_type=row['Employee Type'],
                        resignation_date=row.get('Resignation Date'),
                        valid_from=row.get('Valid From'),
                        valid_to=row.get('Valid To'),
                        country=country,
                        state=state_obj,
                        role=role,
                        salutation=salutation
                    )
                    print(f"Employee created: {employee}")
                    employee.save()
                    print("Employee saved successfully")

                    # Add the created employee to the list
                    # Add these fields to the created_employees list in the view
                    created_employees.append({
                        'employee_id': employee.employee_id,
                        'first_name': employee.first_name,
                        'last_name': employee.last_name,
                        'department': employee.department.dep_name if employee.department else '',
                        'designation': employee.designation,
                        'company_email': employee.company_email,
                        'mobile_phone': employee.mobile_phone
                    })

                except Exception as e:
                    print(f"Error creating employee at row {index + 1}: {str(e)}")
                    return JsonResponse({'error': f"Error creating employee at row {index + 1}: {str(e)}"}, status=400)

            # Return all created employees
            return JsonResponse({'created_employees': created_employees})

        except Exception as e:
            print(f"Failed to process the Excel file: {str(e)}")
            return JsonResponse({'error': f"Failed to process the Excel file: {str(e)}"}, status=400)
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from .models import Employees

class EmployeeExcelUpdateView(View):
    template_name = 'employee_excel_update.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        excel_file = request.FILES.get('excel_file')

        if not excel_file:
            messages.error(request, "Please upload an Excel file.")
            return redirect('employee_excel_update')

        try:
            # Read the Excel file into a DataFrame
            df = pd.read_excel(excel_file)

            # Validate and update each employee
            for index, row in df.iterrows():
                try:
                    employee_id = row['employee_id']
                    employee = Employees.objects.get(employee_id=employee_id)

                    # Update fields
                    employee.first_name = row.get('first_name', employee.first_name)
                    employee.middle_name = row.get('middle_name', employee.middle_name)
                    employee.last_name = row.get('last_name', employee.last_name)
                    employee.company_email = row.get('company_email', employee.company_email)
                    employee.personal_email = row.get('personal_email', employee.personal_email)
                    employee.mobile_phone = row.get('mobile_phone', employee.mobile_phone)
                    employee.office_phone = row.get('office_phone', employee.office_phone)
                    employee.home_phone = row.get('home_phone', employee.home_phone)
                    employee.home_city = row.get('home_city', employee.home_city)
                    employee.home_post_office = row.get('home_post_office', employee.home_post_office)
                    employee.home_house = row.get('home_house', employee.home_house)
                    employee.pincode = row.get('pincode', employee.pincode)
                    employee.department_id = row.get('department_id', employee.department_id)
                    employee.designation = row.get('designation', employee.designation)
                    employee.manager_id = row.get('manager_id', employee.manager_id)
                    employee.employee_status = row.get('employee_status', employee.employee_status)
                    employee.emergency_contact_name = row.get('emergency_contact_name', employee.emergency_contact_name)
                    employee.emergency_contact_phone = row.get('emergency_contact_phone', employee.emergency_contact_phone)
                    employee.emergency_contact_relation = row.get('emergency_contact_relation', employee.emergency_contact_relation)
                    employee.base_salary = row.get('base_salary', employee.base_salary)
                    employee.employee_type = row.get('employee_type', employee.employee_type)
                    employee.resignation_date = row.get('resignation_date', employee.resignation_date)
                    employee.valid_from = row.get('valid_from', employee.valid_from)
                    employee.valid_to = row.get('valid_to', employee.valid_to)
                    employee.country_id = row.get('country_id', employee.country_id)
                    employee.state_id = row.get('state_id', employee.state_id)

                    employee.save()
                except Employees.DoesNotExist:
                    messages.warning(request, f"Employee with ID {employee_id} does not exist.")
                except Exception as e:
                    messages.error(request, f"Error updating employee {employee_id}: {str(e)}")

            messages.success(request, "Employee records updated successfully.")
        except Exception as e:
            messages.error(request, f"Failed to process the Excel file: {str(e)}")

        return redirect('employee_excel_update')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Resume, Certificate  # Import your models

@csrf_exempt
def delete_file(request):
    if request.method == 'POST':
        file_id = request.POST.get('file_id')
        file_type = request.POST.get('file_type')

        try:
            if file_type == 'resume':
                file_instance = Resume.objects.get(id=file_id)
            elif file_type == 'certificate':
                file_instance = Certificate.objects.get(id=file_id)
            else:
                return JsonResponse({'success': False})

            file_instance.delete()
            return JsonResponse({'success': True})
        except (Resume.DoesNotExist, Certificate.DoesNotExist):
            return JsonResponse({'success': False})

    return JsonResponse({'success': False})


#
# from django.http import JsonResponse
# from .models import state
#
# def get_states(request):
#     country_id = request.GET.get('country_id')
#     states = state.objects.filter(country_id=country_id).values('id', 'name')
#     return JsonResponse({'states': list(states)})




# from django.views.generic import DeleteView
# from .models import Employees
#
# class EmployeeDeleteView(DeleteView):
#     model = Employees
#     template_name = 'delete_employee.html'
#     context_object_name = 'data'
#     success_url = reverse_lazy('employee_list')  # Redirect after delete
#
#     #soft delete logic mentioned below
#
#     def delete(self, request, *args, **kwargs):
#         """Mark the employee as deleted instead of deleting from the database."""
#         self.object = self.get_object()
#         self.object.delete()  # Call the soft delete method in the model
#
#
#         return redirect(self.success_url)





from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DeleteView
from django.contrib import messages
from .models import Employees

class EmployeeDeleteView(DeleteView):
    model = Employees
    template_name = 'delete_employee.html'
    context_object_name = 'data'
    success_url = reverse_lazy('employee_list')  # Redirect URL after delete

    def post(self, request, *args, **kwargs):
        """Handle POST request for soft delete and show a success message."""
        employee = get_object_or_404(Employees, pk=self.kwargs['pk'])  # Fetch employee
        emp_name = f"{employee.first_name} {employee.last_name}"  # Get full name

        if not employee.is_deleted:
            employee.is_deleted = True  # Soft delete
            employee.save()
            messages.success(request, f"✅ Employee {emp_name} has been deleted.")  # Success message
        else:
            messages.info(request, "ℹ️ This employee is already deleted.")  # Already deleted message

        return redirect(self.success_url)  # Redirect to employee list
#


from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Employees

def restore_employee(request, pk):
    """Restore a soft-deleted employee."""
    employee = get_object_or_404(Employees, pk=pk)
    if employee.is_deleted:
        employee.is_deleted = False
        employee.save()
        messages.success(request, f"✅ Employee {employee.first_name} {employee.last_name} has been restored.")
    else:
        messages.info(request, "This employee is already active.")
    return redirect('deleted_employees')

from django.views.generic.list import ListView
from .models import Employees

class DeletedEmployeeListView(ListView):
    model = Employees
    template_name = "deleted_employees_display.html"
    context_object_name = "employees"

    def get_queryset(self):
        return Employees.objects.filter(is_deleted=True)

# Admin Dashboard View (after successful login)
from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')  # Render the admin dashboard page


#


from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib import messages
from datetime import timedelta
from .models import LeaveRequest, Employees
from employee_app.models import Holiday, FloatingHoliday

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta

def accept_leave_request(request, leave_request_id):
    if request.method == "POST":
        leave_request = get_object_or_404(LeaveRequest, id=leave_request_id)
        employee = leave_request.employee_master

        # Fetch policy for floating holidays
        floating_entitlement = getattr(employee, 'floating_holidays_balance', 2)  # Or from policy table if relevant

        # Get all holiday/floating dates for efficiency
        holiday_dates = set(Holiday.objects.values_list('date', flat=True))
        floating_dates = set(FloatingHoliday.objects.values_list('date', flat=True))

        casual_days = 0
        floating_days = 0

        floating_h_used = employee.floating_holidays_used  # initial used

        current_date = leave_request.start_date
        while current_date <= leave_request.end_date:
            if current_date.weekday() in [5, 6]:  # weekend
                current_date += timedelta(days=1)
                continue
            if current_date in holiday_dates:
                current_date += timedelta(days=1)
                continue
            if current_date in floating_dates and floating_h_used + floating_days < floating_entitlement:
                floating_days += 1
                current_date += timedelta(days=1)
                continue
            casual_days += 1
            current_date += timedelta(days=1)

        # Check employee has enough balance
        if employee.used_leaves + casual_days > employee.total_leaves:
            messages.error(request, "Employee cannot exceed the allowed casual leave days.")
            return redirect('leave_request_display')
        if employee.floating_holidays_used + floating_days > employee.floating_holidays_balance:
            messages.error(request, "Employee cannot exceed the allowed floating holidays.")
            return redirect('leave_request_display')

        # Update leave usage
        employee.used_leaves += casual_days
        employee.floating_holidays_used += floating_days
        employee.save()

        # Update leave request (status, approver, leave_days)
        leave_request.status = "Accepted"
        leave_request.approved_by = request.user
        leave_request.leave_days = casual_days + floating_days  # or just "leave_days" if consistent
        leave_request.save()

        # Email
        employee_email = employee.user.email
        subject = "Leave Request Approved"
        message = (
            f"Dear {employee.user.first_name},\n\n"
            f"Your leave request from {leave_request.start_date} to {leave_request.end_date} has been approved.\n"
            f"Status: Approved\n"
            f"Enjoy your leave!\n\n"
            f"Best Regards,\nYour Leave Management System"
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [employee_email])
        messages.success(request, "The leave request has been accepted.")

        return redirect('leave_request_display')

    return HttpResponse("Invalid Request", status=400)


def reject_leave_request(request, leave_request_id):
    if request.method == "POST":
        leave_request = get_object_or_404(LeaveRequest, id=leave_request_id)
        leave_request.status = "Rejected"
        leave_request.approved_by = request.user  # Set who approved
        leave_request.save()

        # Fetch employee's email
        employee_email = leave_request.employee_master.user.email  # Assuming `user` is a related field

        # Email content
        subject = "Leave Request Rejected"
        message = (
            f"Dear {leave_request.employee_master.user.first_name},\n\n"
            f"Your leave request from {leave_request.start_date} to {leave_request.end_date} has been rejected by the admin.\n"
            f"Status: Rejected\n"
            f"If you have any questions, please contact HR.\n\n"
            f"Best Regards,\nYour Leave Management System"
        )

        # Send email
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [employee_email])
        messages.success(request, "The leave request has been rejected.")

        return redirect('leave_request_display')  # Redirect back to the display page

    return HttpResponse("Invalid Request", status=400)



from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

def admin_logout(request):
    logout(request)  # Logs out the admin user
    return redirect('admin_login')  # Redirect to the admin login page after logout




  # Ensure this form is correctly defined in your forms.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from datetime import datetime
from .models import Holiday, FloatingHoliday
from .forms import Holiday_Form

def add_holidays(request):
    current_year = datetime.now().year

    if request.method == "POST":
        form = Holiday_Form(request.POST)
        if form.is_valid():
            leave_type = form.cleaned_data['leave_type']
            name = form.cleaned_data['name']
            selected_date = form.cleaned_data['date']
            selected_year = selected_date.year
            selected_day = selected_date.strftime("%A")

            if leave_type == 'fixed':
                if Holiday.objects.filter(date=selected_date).exists():
                    messages.warning(request, "⚠️ The date you have entered is already added as a Fixed Holiday.")
                else:
                    Holiday.objects.create(date=selected_date, name=name, day=selected_day, year=selected_year)
                    messages.success(request, "✅ Fixed holiday added successfully!")

            elif leave_type == 'floating':
                if FloatingHoliday.objects.filter(date=selected_date).exists():
                    messages.warning(request, "⚠️ The date you have entered is already added as a Floating Holiday.")
                else:
                    FloatingHoliday.objects.create(name=name, date=selected_date, year=selected_year)
                    messages.success(request, "✅ Floating holiday added successfully!")

            return redirect('add_holidays')

    else:
        form = Holiday_Form()

    # Fetch holidays for the current year
    fixed_holidays = Holiday.objects.filter(year=current_year)
    floating_holidays = FloatingHoliday.objects.filter(year=current_year)

    context = {
        'form': form,
        'fixed_holidays': fixed_holidays,
        'floating_holidays': floating_holidays,
        'current_year': current_year,
    }

    return render(request, 'add_holidays.html', context)

from django.http import JsonResponse
from .models import Holiday, FloatingHoliday

def filter_holidays_by_year(request, year):
    holiday_type = request.GET.get('type', '')  # Get the type from the query parameters
    holidays = []

    if holiday_type == 'fixed' or holiday_type == '':
        # Order fixed holidays by date in ascending order
        fixed_holidays = Holiday.objects.filter(date__year=year).order_by('date')
        holidays.extend([{
            'name': holiday.name,
            'date': holiday.date.strftime('%Y-%m-%d'),
            'type': 'Fixed'
        } for holiday in fixed_holidays])

    if holiday_type == 'floating' or holiday_type == '':
        # Order floating holidays by date in ascending order
        floating_holidays = FloatingHoliday.objects.filter(date__year=year).order_by('date')
        holidays.extend([{
            'name': holiday.name,
            'date': holiday.date.strftime('%Y-%m-%d'),
            'type': 'Floating'
        } for holiday in floating_holidays])

    return JsonResponse({'holidays': holidays})


from .forms import *
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash

@login_required
def change_password(request):
    """Allow admin to change password without requiring old password."""
    if request.method == 'POST':
        form = AdminPasswordChangeForm(request.POST, user=request.user)  # Pass user
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user = request.user
            user.set_password(new_password)  # Change password
            user.save()
            update_session_auth_hash(request, user)  # Prevent logout
            return redirect('admin_index')  # Redirect to profile after success
    else:
        form = AdminPasswordChangeForm(user=request.user)  # Pass user to form

    return render(request, 'change_password.html', {'form': form})






def mainbase_view(request):
    return render(request,'admin_partials/admin_base.html')


# from django.http import JsonResponse
# from .models import state  # ✅ Ensure correct import
#
# def get_states_by_country(request):
#     country_id = request.GET.get('country_id')
#     if country_id:
#         states = state.objects.filter(country_id=country_id).values('id', 'name')
#         return JsonResponse({'states': list(states)})
#     return JsonResponse({'states': []})


from django.http import JsonResponse
from django.shortcuts import render
from .models import state  # Ensure the correct model name


def load_states(request):
    country_id = request.GET.get('country_id')
    if country_id:
        states = state.objects.filter(country_id=country_id).order_by('name').values('id', 'name')
        return JsonResponse({'states': list(states)})  # ✅ Return JSON response

    return JsonResponse({'states': []})  # ✅ Return empty list if no country selected

#



from django.shortcuts import render
from django.http import JsonResponse
from .models import LeaveRequest
from django.shortcuts import render
from .models import LeaveRequest, Employees

def admin_leave_requests(request):
    print("🚀 Debug - View is being called!")  # Check if the view is triggered

    # Use select_related to optimize database queries
    leave_requests = LeaveRequest.objects.select_related('employee_user', 'employee_master').all()

    # Extract available years for filtering dropdown
    available_years = list(set(leave_requests.values_list('start_date__year', flat=True)))
    print("🚀 Debug - Available Years:", available_years)  # Debugging

    leave_requests_data = [
        {
            "employee_name": (
                f"{leave_request.employee_master.first_name} {leave_request.employee_master.last_name}"
                if leave_request.employee_master else "Not Available"
            ),
            "employee_email": leave_request.employee_user.email if leave_request.employee_user else "Not Available",
            "leave_request": leave_request,
        }
        for leave_request in leave_requests
    ]

    return render(request, "leave_request_display.html", {
        "leave_requests_data": leave_requests_data,
        "available_years": sorted(available_years, reverse=True),  # Ensure years are sorted in descending order
    })
from django.http import JsonResponse
from django.db.models import Q
from .models import LeaveRequest





def filter_leave_requests(request):
    year = request.GET.get('year', None)
    employee_name = request.GET.get('employee_name', '')
    status = request.GET.get('status', '')  # Add this line

    leave_requests = LeaveRequest.objects.select_related('employee_master').all()

    if year:
        leave_requests = leave_requests.filter(start_date__year=year)

    if employee_name:
        leave_requests = leave_requests.filter(
            Q(employee_master__emp_fname__icontains=employee_name) |
            Q(employee_master__emp_lname__icontains=employee_name)
        )

    if status:  # Add this condition
        leave_requests = leave_requests.filter(status=status)

    filtered_data = [
        {
            'id': leave.id,
            'employee_name': f"{leave.employee_master.first_name} {leave.employee_master.last_name}".strip() if leave.employee_master else "Not Available",
            'employee_email': leave.employee_master.personal_email if leave.employee_master else "Not Available",
            'leave_type': leave.leave_type,
            'start_date': leave.start_date.strftime('%Y-%m-%d'),
            'end_date': leave.end_date.strftime('%Y-%m-%d'),
            'reason': leave.reason,
            'status': leave.status,
        }
        for leave in leave_requests
    ]

    return JsonResponse(filtered_data, safe=False)





from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages


def admin_login(request):
    if request.method == 'POST':
        identifier = request.POST.get('username')  # Username or email
        password = request.POST.get('password')

        # Check if it's an email or username
        user = None
        if '@' in identifier:  # If email
            try:
                user = User.objects.get(email=identifier)
                username = user.username  # Get username from email
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or username')
                return redirect('admin_login')
        else:
            username = identifier  # Treat input as username

        # Authenticate
        user = authenticate(request, username=username, password=password)

        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect('admin_index')  # Redirect to admin dashboard
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions')

    return render(request, 'admin_login.html')  # Render login page




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Employees # Import your Employee model

@csrf_exempt
def generate_emp_id(request):
    """
    Generates a unique Employee ID based on the selected employee type.
    """
    if request.method == "GET":
        employee_type = request.GET.get("employee_type", "").strip()

        if not employee_type:
            return JsonResponse({"error": "Missing employee_type parameter"}, status=400)

        # Get the latest employee ID of the given type
        last_employee = Employees.objects.filter(employee_id__startswith=employee_type).order_by("-employee_id").first()

        if last_employee:
            # Extract the numeric part and increment
            last_number = int(last_employee.employee_id.split("-")[1])
            new_number = last_number + 1
        else:
            new_number = 100000 # Start from 1000 if no previous records exist

        # Generate the new Employee ID
        new_emp_id = f"{employee_type}{new_number}"

        return JsonResponse({"emp_id": new_emp_id})

    return JsonResponse({"error": "Invalid request method"}, status=405)


from django.http import JsonResponse
from .models import Holiday, FloatingHoliday

from django.http import JsonResponse
from .models import Holiday, FloatingHoliday

