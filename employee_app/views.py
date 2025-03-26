from django.shortcuts import render

# Create your views here.


# views.py


# views.py
# employee_app/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages




from django.contrib.auth import authenticate, login
from django.contrib import messages

def employee_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')  # emp_email
        password = request.POST.get('password')

        # Authenticate with email as the username
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)  # Log the user in

            #django initially takes password in a hashed format
            # # Check if the user has set a password (not the default password)
            # if user.password == 'defaultpassword':  # If password is default
            #     return redirect('set_password')  # Redirect to the set password page

            if user.check_password("defaultpassword"):
                return redirect('set_password')  # Redirect to the set password page

            return redirect('index')  # Redirect to employee dashboard
        else:
            messages.error(request, 'Invalid credentials')
            # return HttpResponse("invalid credentials")
            return redirect('login')  # Redirect back to login page

    return render(request, 'emp_login.html')






# employee_app/views.py







#
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth import update_session_auth_hash
# from django.contrib import messages
# from django.shortcuts import render, redirect
# from .forms import CustomPasswordChangeForm  # Import the custom form
#
# @login_required
# def set_password(request):
#     if request.method == 'POST':
#         form = CustomPasswordChangeForm(request.user, request.POST)  # Use the custom form
#
#         if form.is_valid():
#             form.save()
#             update_session_auth_hash(request, form.user)  # Keep the user logged in
#             messages.success(request, 'Your password has been updated!')
#             return redirect('index')
#         else:
#             messages.error(request, 'Please correct the errors below.')
#     else:
#         form = CustomPasswordChangeForm(request.user)
#
#     # Clear messages before rendering the page
#     storage = messages.get_messages(request)
#     storage.used = True
#
#     return render(request, 'set_password.html', {'form': form})






from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CustomPasswordChangeForm  # Your custom form
from admin_app.models import Employees  # Import your Employees model

@login_required
def set_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            new_password = form.cleaned_data.get('new_password1')  # Get the new password

            # Save the new password (hashed) to the User model
            user = form.save()

            # Store plain text password in Employees model
            try:
                employee = Employees.objects.get(user=request.user)  # Get employee record
                employee.emp_password = new_password  # Store plain text password
                employee.save()
            except Employees.DoesNotExist:
                messages.error(request, "Employee record not found!")

            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, 'Your password has been updated!')
            return redirect('index')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)

    # Clear messages before rendering the page
    storage = messages.get_messages(request)
    storage.used = True

    return render(request, 'set_password.html', {'form': form})










# employee_app/auth_backends.py

from django.contrib.auth.backends import ModelBackend
from admin_app.models import Employees  # Import Employees model


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = Employees.objects.get(emp_email=username)  # Assuming emp_email is the email field
            if user.check_password(password):  # Check if password matches
                return user
        except Employees.DoesNotExist:
            return None




# employee_app/views.py
#
# from django.shortcuts import render, get_object_or_404
# from .models import Employees
#
# def employee_dashboard(request):
#     employee = get_object_or_404(Employees, emp_email=request.user.username)
#     return render(request, 'emp_profile.html', {'employee': employee})



from django.shortcuts import render, get_object_or_404
from .models import Employees

def employee_dashboard(request):
    # Fetch the logged-in employee
    employee = get_object_or_404(Employees, emp_email=request.user.username)

    # Check if the employee is a manager (i.e., has subordinates)
    is_manager = Employees.objects.filter(employee_manager=employee).exists()

    current_year = now().year  # Get current year
    total_used_leaves = employee.emp_used_leaves  # Fetch from the Employees model

    return render(request, 'emp_profile.html', {
        'employee': employee,
        'is_manager': is_manager,
        'emp_id': employee.emp_id,  # Employee ID
        'emp_fname': employee.emp_fname,  # Employee first name
        'emp_lname': employee.emp_lname,  # Employee last name
        'emp_designation': employee.designation  ,# Employee designation
        'total_used_leaves' : total_used_leaves
    })







# employee_app/views.py

# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from .models import Employees

# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from .models import Employees
#
# @login_required
# def employee_dashboard(request):
#     # Fetch the logged-in employee details using the logged-in user's email
#     employee = Employees.objects.get(emp_email=request.user.username)
#
#     # Pass the employee object to the template
#     return render(request, 'emp_profile.html', {'employee': employee})
#
#     # Prevent caching
#     response['Cache-Control'] = 'no-store'
#     response['Pragma'] = 'no-cache'
#     response['Expires'] = '0'
#
#     return response






from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponse
from .models import Employees

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Employees
import random
import string

# Function to generate a random password
from django.contrib.auth.models import User
from django.http import HttpResponse
from .models import Employees
import random
import string

# Function to generate a random password
def generate_random_password(length=8):
    """Generate a random password with letters and digits."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

# View to update passwords for all employees
def update_employee_passwords(request):
    # Ensure that only superusers or admins can access this view
    if not request.user.is_superuser:
        return HttpResponse('Permission denied', status=403)

    # Loop through all employees
    employees = Employees.objects.all()
    updated_count = 0

    # Set password for each employee
    for employee in employees:
        if employee.user:  # Ensure employee has an associated User
            new_password = generate_random_password()  # Generate a random password
            employee.user.set_password(new_password)  # Set the new password
            employee.user.save()  # Save the updated user
            updated_count += 1

    return HttpResponse(f'Passwords updated successfully for {updated_count} employees.')






# views.py (in employee_app)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import EmployeeEditForm
from .models import Employees

# @login_required
# def edit_employee_profile(request):
#     employee = Employees.objects.get(emp_email=request.user.username)
#
#     if request.method == 'POST':
#         form = EmployeeEditForm(request.POST, instance=employee)
#         if form.is_valid():
#             form.save()  # Save the updated employee profile
#             return redirect('profile')  # Redirect to the profile page after saving
#     else:
#         form = EmployeeEditForm(instance=employee)  # Initialize the form with the current employee data
#
#     return render(request, 'edit_profile.html', {'form': form})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Employees, Country, state
from .forms import EmployeeEditForm

@login_required
def edit_employee_profile(request):
    # Get the employee object based on the logged-in user
    employee = get_object_or_404(Employees, emp_email=request.user.username)

    if request.method == 'POST':
        # Handle the form submission
        form = EmployeeEditForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()  # Save the updated employee profile
            return redirect('profile')  # Redirect to the profile page after saving
    else:
        # Initialize the form with the current employee data
        form = EmployeeEditForm(instance=employee)

    # Get all countries for the country dropdown
    countries = Country.objects.all()

    # Prefetch states for the currently selected country in the employee profile
    states = state.objects.filter(country=employee.country) if employee.country else state.objects.none()

    # Render the template with the form, countries, and states
    return render(request, 'edit_profile.html', {
        'form': form,
        'countries': countries,
        'states': states,
    })



# employee_app/views.py
from django.shortcuts import redirect
from django.contrib.auth import logout

def employee_logout(request):
    logout(request)  # Logs out the employee
    return redirect('login')  # Redirect to login page after logout



from django.http import JsonResponse
# from admin_app.models import state

# def get_states(request):
#     country_id = request.GET.get('country_id')
#     if country_id:
#         states = state.objects.filter(country_id=country_id).values('id', 'name')
#         return JsonResponse({'states': list(states)})
#     return JsonResponse({'states': []})  # Return an empty list if no country is selected


# from django.http import JsonResponse
# from .models import state
#
# from django.http import JsonResponse
# from .models import state
#
#
#
# def get_states(request):
#     country_id = request.GET.get('country_id')  # Get country_id from the request
#     if country_id:
#         # Fetch states for the selected country
#         states = state.objects.filter(country_id=country_id).values('id', 'name')
#         return JsonResponse({'states': list(states)})  # Return states as JSON
#     return JsonResponse({'states': []})  # Return empty list if no country selected




# password change view

# main password_change view

# from .forms import *
# from django.shortcuts import render, redirect
# from django.contrib.auth.forms import PasswordChangeForm
# from django.contrib.auth import update_session_auth_hash
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from datetime import datetime
#
# @login_required
# def change_password(request):
#     if request.method == 'POST':
#         form = PasswordChangeForm(user=request.user, data=request.POST)
#         if form.is_valid():
#             form.save()  # Save the new password
#             update_session_auth_hash(request, form.user)  # Keep the user logged in after password change
#             messages.success(request, 'Your password was successfully updated!')
#             return redirect('index')  # Redirect to the profile or another page
#         else:
#             messages.error(request, 'Please correct the error below.')
#     else:
#         form = PasswordChangeForm(user=request.user)
# #
#     return render(request, 'change_password.html', {'form': form})



from .forms import *
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Employees

@login_required
def change_password(request):
    try:
        # Fetch the logged-in employee
        employee = Employees.objects.get(emp_email=request.user.username)
    except Employees.DoesNotExist:
        return render(request, 'employee_app/error.html', {'message': 'Employee profile not found.'})

    # Check if the employee is a manager
    is_manager = Employees.objects.filter(employee_manager=employee).exists()

    # Fetch total used leaves directly from the Employees model
    total_used_leaves = employee.emp_used_leaves

    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()  # Save the new password
            update_session_auth_hash(request, form.user)  # Keep the user logged in after password change
            messages.success(request, 'Your password was successfully updated!')
            return redirect('index')  # Redirect to the profile or another page
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'change_password.html', {
        'form': form,
        'is_manager': is_manager,
        'emp_id': employee.emp_id,  # Employee ID
        'emp_fname': employee.emp_fname,  # Employee first name
        'emp_lname': employee.emp_lname,  # Employee last name
        'emp_designation': employee.designation,  # Employee designation
        'total_used_leaves': total_used_leaves  # Fetching from Employees model
    })



# requesting leave view fn


from datetime import date, timedelta
from calendar import SATURDAY, SUNDAY
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .forms import LeaveRequestForm
from .models import Employees, Holiday, FloatingHoliday, LeaveRequest
import json
from django.db.models import Sum, F
from datetime import timedelta
from datetime import datetime


@login_required
def request_leave(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, user=request.user)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.employee_user = request.user

            # Fetch employee details
            try:
                employee = Employees.objects.get(emp_email=request.user.email)
                leave_request.employee_master = employee
            except Employees.DoesNotExist:
                return render(request, 'employee_app/error.html', {'message': 'Employee details not found.'})

            # Calculate leave duration
            start_date = leave_request.start_date
            end_date = leave_request.end_date
            leave_duration = (end_date - start_date).days + 1

            # Check if leave duration exceeds available balance
            if leave_duration > employee.available_leaves():
                messages.error(request, 'Your requested leave exceeds your remaining leave balance.')
                return redirect('request_leave')

            # Validate leave type
            leave_type = request.POST.get('leave_type')
            floating_holidays = list(FloatingHoliday.objects.values_list('date', flat=True))

            if leave_type == "Floating Leave":
                invalid_dates = [date for date in daterange(start_date, end_date) if date not in floating_holidays]
                if invalid_dates:
                    messages.error(request, 'The requested date range contains dates other than floating holidays.')
                    return redirect('request_leave')

            elif leave_type == "Casual Leave":
                invalid_dates = [date for date in daterange(start_date, end_date) if date in floating_holidays]
                if invalid_dates:
                    messages.error(request, 'The requested date range contains floating holidays.')
                    return redirect('request_leave')

            # Save the leave request if all validations pass
            leave_request.status = 'Pending'
            leave_request.save()
            messages.success(request, 'Leave request submitted successfully!')
            # return HttpResponse("Submitted successfully")
            return redirect('request_leave')
    else:
        form = LeaveRequestForm(user=request.user)

    # Retrieve employee details
    try:
        employee = Employees.objects.get(emp_email=request.user.email)
    except Employees.DoesNotExist:
        return render(request, 'employee_app/error.html', {'message': 'Employee details not found.'})

    # Determine if the user is a manager
    is_manager = Employees.objects.filter(employee_manager=employee).exists()




    # Current year and month
    current_year = date.today().year
    today = date.today()
    current_month = today.month

    total_used_leaves = LeaveRequest.objects.filter(
        employee_master=employee,
        status='Accepted',
        start_date__year=current_year
    ).aggregate(total_days=Sum(F('end_date') - F('start_date') + timedelta(days=1)))['total_days'] or 0

    # Fetch holidays and floating holidays
    holidays = list(Holiday.objects.filter(date__year=current_year).values_list('date', flat=True))
    floating_holidays = list(FloatingHoliday.objects.filter(date__year=current_year).values_list('date', flat=True))

    # Fetch approved leave dates for the employee
    approved_leave_dates = list(LeaveRequest.objects.filter(
        employee_user=request.user, status='Accepted'
    ).values_list('start_date', 'end_date'))

    # Flatten the approved leave date range
    approved_leave_dates = [
        d.strftime('%Y-%m-%d') for start, end in approved_leave_dates for d in daterange(start, end)
    ]

    # Before returning the context to the template
    print("Approved Leave Dates:", approved_leave_dates)

    # Calculate weekends in the current month
    weekends = []
    day = date(current_year, current_month, 1)
    while day.month == current_month:
        if day.weekday() in [SATURDAY, SUNDAY]:  # Saturday = 5, Sunday = 6
            weekends.append(day)
        day += timedelta(days=1)



    # Format dates and serialize them for JavaScript
    holidays = json.dumps([d.strftime('%Y-%m-%d') for d in holidays])
    floating_holidays = json.dumps([d.strftime('%Y-%m-%d') for d in floating_holidays])
    weekends = json.dumps([d.strftime('%Y-%m-%d') for d in weekends])
    approved_leave_dates = json.dumps(approved_leave_dates)

    # Render the template with serialized data
    return render(request, 'test4.html', {
        'form': form,
        'employee_name': f"{employee.emp_fname} {employee.emp_lname}",
        'employee_email': employee.emp_email,
        'holidays': holidays,
        'floating_holidays': floating_holidays,
        'weekends': weekends,
        'approved_leave_dates': approved_leave_dates,  # Pass approved leave dates to the template
        'is_manager': is_manager,
        'total_used_leaves': total_used_leaves,
        'emp_designation': employee.designation,  # Employee designation
        'emp_id': employee.emp_id,  # Employee ID
        'emp_fname': employee.emp_fname,  # employee firstname
        'emp_lname': employee.emp_lname  # employee lastname
    })


# Utility function to generate a date range
def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)













# view for debugging

from django.shortcuts import render
from .models import Holiday, FloatingHoliday
import json

def calendar_view(request):
    current_year = 2025  # Change this dynamically if needed

    # Fetch holidays and floating holidays for the current year
    holidays = list(Holiday.objects.filter(year=current_year).values_list('date', flat=True))
    floating_holidays = list(FloatingHoliday.objects.filter(year=current_year).values_list('date', flat=True))

    # Convert date format to string (YYYY-MM-DD)
    holidays = [date.strftime('%Y-%m-%d') for date in holidays]
    floating_holidays = [date.strftime('%Y-%m-%d') for date in floating_holidays]

    print("Holidays from DB:", holidays)
    print("Floating Holidays from DB:", floating_holidays)

    return render(request, 'calendar.html', {
        'holidays': json.dumps(holidays),
        'floating_holidays': json.dumps(floating_holidays),
    })







# main leave history view



from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import LeaveRequest

@login_required
def my_leave_history(request):
    # Fetch the leave requests for the logged-in user
    leave_requests = LeaveRequest.objects.filter(employee_user=request.user).order_by('-start_date')

    # Check if the user is a manager
    try:
        employee = Employees.objects.get(user=request.user)
        subordinates = employee.employees_managed.all()  # Get all employees where this user is the manager
        is_manager = subordinates.exists()  # Check if there are any subordinates
    except Employees.DoesNotExist:
        subordinates = None
        is_manager = False


    current_year = now().year  # Get current year
    total_used_leaves = employee.emp_used_leaves  # Fetch from the Employees model

    return render(request, 'my_leave_history.html', {'leave_requests': leave_requests,'is_manager': is_manager, 'emp_designation': employee.designation,  # Employee designation
        'emp_id': employee.emp_id,  # Employee ID
        'emp_fname' : employee.emp_fname, #employee firstname
        'emp_lname' : employee.emp_lname ,'total_used_leaves' : total_used_leaves}) #employee lastname })# Pass this to the template




from django.utils.timezone import now

def emp_index(request):
    try:
        employee = Employees.objects.get(emp_email=request.user.username)
    except Employees.DoesNotExist:
        return render(request, 'error.html', {'message': 'Employee not found.'})

    # Check if the employee is a manager (has subordinates)
    if employee.employees_managed.exists():  # If there are employees managed by this employee
        is_manager = True
    else:
        is_manager = False

    # Get total used leaves for the current year
    current_year = now().year  # Get current year
    total_used_leaves = employee.emp_used_leaves  # Fetch from the Employees model

    return render(request, 'partials/base.html', {
        'employee': employee,
        'is_manager': is_manager , # Pass whether the employee is a manager or not
        'total_used_leaves': total_used_leaves , # Pass the used leaves count to the template
        'emp_designation': employee.designation,  # Employee designation
        'emp_id': employee.emp_id,  # Employee ID
        'emp_fname' : employee.emp_fname, #employee firstname
        'emp_lname' : employee.emp_lname #employee lastname
    })



from django.db.models import Sum
from datetime import date

def get_total_leaves(employee, year=None):
    """Fetch total approved leave days for the given employee in a specific year."""
    if year is None:
        year = date.today().year  # Default to the current year

    # Filter by employee_master and year
    leaves = LeaveRequest.objects.filter(
        employee_master=employee,
        status='Approved',
        start_date__year=year
    )

    # Calculate the total days of leave
    total_days = sum(leave.calculate_total_days() for leave in leaves)
    return total_days



from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Employees  # Import Employees model

@login_required
def total_leaves_view(request):
    user = request.user
    # Fetch the related Employees object
    employee = get_object_or_404(Employees, user=user)  # Adjust based on the relationship in Employees

    current_year = date.today().year
    total_leaves = get_total_leaves(employee, year=current_year)

    return render(request, 'total_leaves.html', {'total_leaves': total_leaves, 'year': current_year})




# to get all the holidays in a year

from django.shortcuts import render
from datetime import date
from .models import Holiday, FloatingHoliday
from datetime import datetime

def holiday_list(request):
    current_year = date.today().year  # Get the current year

    # Filter holidays and floating holidays for the current year
    holidays = Holiday.objects.filter(date__year=current_year)
    floating_holidays = FloatingHoliday.objects.filter(date__year=current_year)

    # Check if the logged-in user is a manager
    is_manager = False  # Default value
    if request.user.is_authenticated:
        try:
            employee = Employees.objects.get(emp_email=request.user.email)
            is_manager = employee.employees_managed.exists()  # Checks if they manage anyone
        except Employees.DoesNotExist:
            pass  # If no employee record is found, keep is_manager as False

    current_year = now().year  # Get current year
    total_used_leaves = employee.emp_used_leaves  # Fetch from the Employees model

    context = {
        'holidays': holidays,
        'floating_holidays': floating_holidays,
        'is_manager': is_manager,  # Pass manager status to template
        'emp_designation': employee.designation,  # Employee designation
        'emp_id': employee.emp_id,  # Employee ID
        'emp_fname': employee.emp_fname,  # employee firstname
        'emp_lname': employee.emp_lname , # employee lastname
        'total_used_leaves' : total_used_leaves
    }
    return render(request, 'holiday_list.html', context)






# manager approver feature-main code

#
# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.auth.decorators import login_required
# from .models import LeaveRequest, Employees
# from datetime import datetime
#
# @login_required
# def manager_leave_requests(request):
#     """View to list leave requests submitted by subordinates."""
#     try:
#         # Fetch the logged-in user's employee profile
#         manager = Employees.objects.get(user=request.user)
#     except Employees.DoesNotExist:
#         return render(request, 'employee_app/error.html', {'message': 'Manager profile not found.'})
#
#     #requirement -for only managers could see the manager request view page
#     # Ensure the logged-in user is a manager (i.e., they manage other employees)
#     if not Employees.objects.filter(employee_manager=manager).exists():
#         # If the logged-in user does not manage any employees, they are not a manager
#         # return redirect('emp_profile')
#         return HttpResponse("cannot access")
#
#     # Check if the employee is a manager (i.e., has employees reporting to them)
#     is_manager = Employees.objects.filter(employee_manager=manager).exists()
#
#     current_year = now().year  # Get current year
#     total_used_leaves = manager.emp_used_leaves  # Fetch from the Employees model
#
#
#
#
#     # Filter leave requests for employees managed by the logged-in manager
#     leave_requests = LeaveRequest.objects.filter(employee_master__employee_manager=manager)
#
#     return render(request, 'manager_leave_requests.html', {
#         'leave_requests': leave_requests,
#         'manager_name': f"{manager.emp_fname} {manager.emp_lname}",
#         'is_manager':is_manager,
#         'emp_designation': manager.designation,  # Employee designation
#         'emp_id': manager.emp_id,  # Employee ID
#         'emp_fname': manager.emp_fname,  # employee firstname
#         'emp_lname': manager.emp_lname  ,# employee lastname
#         'total_used_leaves' : total_used_leaves
#     })
#


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from .models import LeaveRequest, Employees
from datetime import datetime
from django.utils.timezone import now


@login_required
def manager_leave_requests(request):
    """View to list leave requests submitted by subordinates."""
    try:
        # Fetch the logged-in user's employee profile
        manager = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        return render(request, 'employee_app/error.html', {'message': 'Manager profile not found.'})

    # Ensure the logged-in user is a manager
    if not Employees.objects.filter(employee_manager=manager).exists():
        return HttpResponse("cannot access")

    # Check if the employee is a manager
    is_manager = Employees.objects.filter(employee_manager=manager).exists()

    current_year = now().year
    total_used_leaves = manager.emp_used_leaves

    # Filter leave requests for employees managed by the logged-in manager
    leave_requests = LeaveRequest.objects.filter(employee_master__employee_manager=manager)

    # Get available years for filtering
    available_years = list(set(leave_requests.values_list('start_date__year', flat=True)))

    return render(request, 'manager_leave_requests.html', {
        'leave_requests': leave_requests,
        'manager_name': f"{manager.emp_fname} {manager.emp_lname}",
        'is_manager': is_manager,
        'emp_designation': manager.designation,
        'emp_id': manager.emp_id,
        'emp_fname': manager.emp_fname,
        'emp_lname': manager.emp_lname,
        'total_used_leaves': total_used_leaves,
        'available_years': sorted(available_years, reverse=True),  # Add this for year filter
    })


# Add new view for handling filter requests
@login_required
def filter_manager_leave_requests(request):
    try:
        manager = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        return JsonResponse({'error': 'Manager profile not found'}, status=404)

    # Get filter parameters
    year = request.GET.get('year', None)
    employee_name = request.GET.get('employee_name', '')
    status = request.GET.get('status', '')

    # Base queryset - only get leave requests for employees under this manager
    leave_requests = LeaveRequest.objects.filter(employee_master__employee_manager=manager)

    # Apply filters
    if year:
        leave_requests = leave_requests.filter(start_date__year=year)

    if employee_name:
        leave_requests = leave_requests.filter(
            Q(employee_master__emp_fname__icontains=employee_name) |
            Q(employee_master__emp_lname__icontains=employee_name)
        )

    if status:
        leave_requests = leave_requests.filter(status=status)

    # Prepare filtered data for response
    filtered_data = [
        {
            'id': leave.id,
            'employee_name': f"{leave.employee_master.emp_fname} {leave.employee_master.emp_lname}".strip(),
            'leave_type': leave.leave_type,
            'start_date': leave.start_date.strftime('%Y-%m-%d'),
            'end_date': leave.end_date.strftime('%Y-%m-%d'),
            'status': leave.status,
        }
        for leave in leave_requests
    ]

    return JsonResponse(filtered_data, safe=False)






from employee_app.utils import calculate_leave_duration
from datetime import datetime

@login_required
def manage_leave_request(request, leave_request_id):
    leave_request = get_object_or_404(LeaveRequest, id=leave_request_id)

    # Ensure the logged-in manager or admin is allowed to act on this leave request
    if not request.user.is_superuser and leave_request.employee_master.employee_manager.user != request.user:
        return render(request, 'employee_app/error.html', {'message': 'Unauthorized action.'})

        # Get the logged-in employee
    try:
        logged_in_employee = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        return render(request, 'employee_app/error.html', {'message': 'Employee profile not found.'})

        # Check if the logged-in employee is a manager
    is_manager = Employees.objects.filter(employee_manager=logged_in_employee).exists()

    current_year = now().year  # Get current year
    total_used_leaves = logged_in_employee.emp_used_leaves  # Fetch from the Employees model

    if request.method == 'POST':
        action = request.POST.get('action')  # 'accept' or 'reject'
        start_date = leave_request.start_date
        end_date = leave_request.end_date
        employee = leave_request.employee_master

        # Use the calculate_leave_duration function to get the accurate leave days (excluding weekends, holidays)
        leave_duration = 0
        floating_holidays_used = employee.floating_holidays_used
        max_floating_holidays = 2

        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in [5, 6]:  # Weekend (Saturday/Sunday)
                current_date += timedelta(days=1)
                continue
            if current_date in Holiday.objects.values_list('date', flat=True):  # Regular holiday
                current_date += timedelta(days=1)
                continue
            if current_date in FloatingHoliday.objects.values_list('date', flat=True):  # Floating holiday
                if floating_holidays_used < max_floating_holidays:
                    floating_holidays_used += 1
                    current_date += timedelta(days=1)
                    continue
            # Count as a regular leave day
            leave_duration += 1
            current_date += timedelta(days=1)

        print(f"Leave Duration (after exclusions): {leave_duration} days")

        if action == 'accept':
            leave_request.status = 'Accepted'
            print(f"Current Used Leaves: {employee.emp_used_leaves}")
            print(f"Current Total Leaves: {employee.emp_total_leaves}")

            # Check if the employee has enough leave balance
            if employee.emp_used_leaves + leave_duration <= 15:
                # Update leave days and floating holidays used
                employee.emp_used_leaves += leave_duration
                employee.floating_holidays_used = floating_holidays_used
                employee.save()
                print(f"Updated Used Leaves: {employee.emp_used_leaves}")
            else:
                messages.error(request, "Employee cannot exceed the allowed 15 total leave days.")
                return redirect('manager_leave_requests')  # Or redirect to another appropriate view

        elif action == 'reject':
            leave_request.status = 'Rejected'

        # Set `approved_by` to the user who approved or rejected the leave
        if request.user.is_superuser:
            leave_request.approved_by = request.user  # Admin approves
        else:
            approver = leave_request.employee_master.employee_manager.user
            leave_request.approved_by = approver  # Manager approves

        leave_request.save()

        return redirect('manager_leave_requests' if not request.user.is_superuser else 'admin_leave_requests')

    return render(request, 'manage_leave_requests.html', {'leave_request': leave_request,'is_manager' : is_manager ,'emp_designation':logged_in_employee.designation , 'emp_id' : logged_in_employee.emp_id , 'emp_fname' : logged_in_employee.emp_fname , 'emp_lname' : logged_in_employee.emp_lname , 'total_used_leaves' : total_used_leaves})



# @login_required
# def manager_leave_requests(request):
#     """View to list leave requests submitted by subordinates."""
#     try:
#         # Fetch the logged-in user's employee profile
#         manager = Employees.objects.get(user=request.user)
#     except Employees.DoesNotExist:
#         return render(request, 'employee_app/error.html', {'message': 'Manager profile not found.'})
#
#     #requirement -for only managers could see the manager request view page
#     # Ensure the logged-in user is a manager (i.e., they manage other employees)
#     if not Employees.objects.filter(employee_manager=manager).exists():
#         # If the logged-in user does not manage any employees, they are not a manager
#         # return redirect('emp_profile')
#         return HttpResponse("cannot access")
#
#     # Check if the employee is a manager (i.e., has employees reporting to them)
#     is_manager = Employees.objects.filter(employee_manager=manager).exists()
#
#
#
#
#     # Filter leave requests for employees managed by the logged-in manager
#     leave_requests = LeaveRequest.objects.filter(employee_master__employee_manager=manager)
#
#     return render(request, 'manager_leave_requests.html', {
#         'leave_requests': leave_requests,
#         'manager_name': f"{manager.emp_fname} {manager.emp_lname}",
#         'is_manager':is_manager,
#         'emp_designation': manager.designation,  # Employee designation
#         'emp_id': manager.emp_id,  # Employee ID
#         'emp_fname': manager.emp_fname,  # employee firstname
#         'emp_lname': manager.emp_lname  # employee lastname
#     })
#
#
#
# })






def test(request):
    return render(request,'test.html')



# 4-2-2025

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Employees

@login_required
def view_subordinates(request):
    """View to list subordinates of the logged-in manager."""
    try:
        manager = Employees.objects.get(user=request.user)  # Get manager's employee record
    except Employees.DoesNotExist:
        return render(request, 'employee_app/error.html', {'message': 'Employee profile not found.'})

    # Fetch employees who report to this manager
    subordinates = Employees.objects.filter(employee_manager=manager)

    # Check if the logged-in employee is actually a manager
    is_manager = subordinates.exists()  # If they have subordinates, they're a manager

    current_year = now().year  # Get current year
    total_used_leaves = manager.emp_used_leaves  # Fetch from the Employees model

    return render(request, 'view_subordinates.html', {
        'subordinates': subordinates,
        'manager': manager,
        'is_manager' : is_manager,
        'emp_id' : manager.emp_id ,
        'emp_fname' : manager.emp_fname,
        'emp_lname' : manager.emp_lname,
        'emp_designation' : manager.designation,
        'total_used_leaves' : total_used_leaves
    })



#
# from .utils import calculate_leave_duration  # Import your existing function
# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages  # Import the messages framework
# from django.core.mail import send_mail
# from .models import Employees, LeaveRequest
#
# from datetime import datetime
#
#
# @login_required
# def allocate_leave(request, employee_id):
#     """Manager can allocate leave for a subordinate."""
#     manager = get_object_or_404(Employees, user=request.user)
#     employee = get_object_or_404(Employees, id=employee_id, employee_manager=manager)
#
#     current_year = now().year  # Get current year
#     total_used_leaves = employee.emp_used_leaves  # Fetch from the Employees model
#
#
#
#     # Determine if the logged-in user is a manager
#     is_manager = Employees.objects.filter(employee_manager=manager).exists()
#
#     if request.method == "POST":
#         print("form submitted")
#         start_date = request.POST.get("start_date")
#         end_date = request.POST.get("end_date")
#         reason = request.POST.get("reason", "").strip()  # Ensuring reason is not null
#
#         if not start_date or not end_date:
#             messages.error(request, "Both start and end date are required.")
#             return render(request, 'allocate_leave.html', {'employee': employee})
#
#         if not reason:
#             messages.error(request, "Reason is required.")
#             return render(request, 'allocate_leave.html', {'employee': employee})
#
#         start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
#         end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
#
#         # Calculate leave days (excluding holidays, weekends, and floating holidays)
#         leave_days = calculate_leave_duration(start_date, end_date, employee)
#
#         if leave_days <= 0:
#             messages.error(request, "No valid leave days selected.")
#             return render(request, 'allocate_leave.html', {'employee': employee})
#
#         if employee.emp_used_leaves + leave_days > employee.emp_total_leaves:
#             messages.error(request, "Not enough leave balance!")
#             return render(request, 'allocate_leave.html', {'employee': employee})
#
#
#
#         # Create Leave Request
#         LeaveRequest.objects.create(
#             employee_user=employee.user,
#             employee_master=employee,
#             start_date=start_date,
#             end_date=end_date,
#             reason=reason,  # Now it will always have a value
#             leave_type="Manager Allocated",
#             status="Approved"
#         )
#
#         # Update employee leave balance
#         employee.emp_used_leaves += leave_days
#         employee.save()
#
#         # Send email notification
#         send_mail(
#             subject="Leave Allocation Notification",
#             message=f"Dear {employee.emp_fname},\n\nYour manager {manager.emp_fname} {manager.emp_lname} has allocated leave for you from {start_date} to {end_date}.\n\nReason: {reason}.\n\nBest regards,\nHR Team",
#             from_email="ajaykmani2001@gmail.com",
#             recipient_list=[employee.emp_email],
#             fail_silently=False,
#         )
#
#         # Adding success message
#         messages.success(request, f"Leave has been allocated to {employee.emp_fname} {employee.emp_lname}.")
#
#         # Redirect to view subordinates
#         return redirect('view_subordinates')
#
#     return render(request, 'allocate_leave.html', {'employee': employee , 'emp_id' : manager.emp_id , 'emp_fname' : manager.emp_fname , 'emp_lname' : manager.emp_lname ,'emp_designation' : manager.designation , 'total_used_leaves' : total_used_leaves , 'is_manager' : is_manager})
#
#





#
# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.core.mail import send_mail
# from datetime import datetime
# from .models import Employees, LeaveRequest, Holiday, FloatingHoliday
# from admin_app.utils import calculate_leave_days  # Ensure correct function is imported
#
#
# @login_required
# def allocate_leave(request, employee_id):
#     """Manager can allocate leave for a subordinate."""
#     manager = get_object_or_404(Employees, user=request.user)
#     employee = get_object_or_404(Employees, id=employee_id, employee_manager=manager)
#
#     current_year = datetime.now().year  # Get current year
#     total_used_leaves = employee.emp_used_leaves  # Fetch from Employees model
#
#     # Determine if the logged-in user is a manager
#     is_manager = Employees.objects.filter(employee_manager=manager).exists()
#
#     if request.method == "POST":
#         start_date = request.POST.get("start_date")
#         end_date = request.POST.get("end_date")
#         reason = request.POST.get("reason", "").strip()
#
#         if not start_date or not end_date:
#             messages.error(request, "Both start and end date are required.")
#             return render(request, 'allocate_leave.html', {'employee': employee})
#
#         if not reason:
#             messages.error(request, "Reason is required.")
#             return render(request, 'allocate_leave.html', {'employee': employee})
#
#         start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
#         end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
#
#         # Fetch holidays and floating holidays
#         holidays = list(Holiday.objects.values_list("date", flat=True))
#         floating_holidays = list(FloatingHoliday.objects.values_list("date", flat=True))
#
#         # Calculate leave days excluding holidays, floating holidays, and weekends
#         leave_days = calculate_leave_days(start_date, end_date, holidays, floating_holidays)
#
#         if leave_days <= 0:
#             messages.error(request, "No valid leave days selected.")
#             return render(request, 'allocate_leave.html', {'employee': employee})
#
#         if employee.emp_used_leaves + leave_days > employee.emp_total_leaves:
#             messages.error(request, "Not enough leave balance!")
#             return render(request, 'allocate_leave.html', {'employee': employee})
#
#         # Create Leave Request
#         LeaveRequest.objects.create(
#             employee_user=employee.user,
#             employee_master=employee,
#             start_date=start_date,
#             end_date=end_date,
#             reason=reason,
#             leave_type="Manager Allocated",
#             status="Approved"
#         )
#
#         # Update employee leave balance
#         employee.emp_used_leaves += leave_days
#         employee.save()
#
#         # Send email notification
#         send_mail(
#             subject="Leave Allocation Notification",
#             message=f"Dear {employee.emp_fname},\n\nYour manager {manager.emp_fname} {manager.emp_lname} has allocated leave for you from {start_date} to {end_date}.\n\nReason: {reason}.\n\nBest regards,\nHR Team",
#             from_email="ajaykmani2001@gmail.com",
#             recipient_list=[employee.emp_email],
#             fail_silently=False,
#         )
#
#         messages.success(request, f"Leave has been allocated to {employee.emp_fname} {employee.emp_lname}.")
#         return redirect('view_subordinates')
#
#     return render(request, 'allocate_leave.html', {
#         'employee': employee,
#         'emp_id': manager.emp_id,
#         'emp_fname': manager.emp_fname,
#         'emp_lname': manager.emp_lname,
#         'emp_designation': manager.designation,
#         'total_used_leaves': total_used_leaves,
#         'is_manager': is_manager
#     })
#





from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from datetime import datetime
from .models import Employees, LeaveRequest, Holiday, FloatingHoliday
from admin_app.utils import calculate_leave_days  # Ensure correct function is imported


@login_required
def allocate_leave(request, employee_id):
    """Manager can allocate leave for a subordinate."""
    manager = get_object_or_404(Employees, user=request.user)
    employee = get_object_or_404(Employees, id=employee_id, employee_manager=manager)

    current_year = datetime.now().year  # Get current year
    total_used_leaves = employee.emp_used_leaves  # Fetch from Employees model

    # Determine if the logged-in user is a manager
    is_manager = Employees.objects.filter(employee_manager=manager).exists()

    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        reason = request.POST.get("reason", "").strip()

        if not start_date or not end_date:
            messages.error(request, "Both start and end date are required.")
            return render(request, 'allocate_leave.html', {'employee': employee})

        if not reason:
            messages.error(request, "Reason is required.")
            return render(request, 'allocate_leave.html', {'employee': employee})

        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Fetch holidays and floating holidays
        holidays = list(Holiday.objects.values_list("date", flat=True))
        floating_holidays = list(FloatingHoliday.objects.values_list("date", flat=True))

        # Calculate total leave days, excluding holidays and weekends
        leave_days = calculate_leave_days(start_date, end_date, holidays, floating_holidays)

        if leave_days <= 0:
            messages.error(request, "No valid leave days selected.")
            return render(request, 'allocate_leave.html', {'employee': employee})

        floating_days_in_request = sum(1 for day in floating_holidays if start_date <= day <= end_date)

        # Check how many floating holidays have been used
        if floating_days_in_request > 0:
            remaining_floating_balance = max(0, employee.floating_holidays_balance - employee.floating_holidays_used)

            if floating_days_in_request <= remaining_floating_balance:
                # Deduct only from floating holidays used
                employee.floating_holidays_used += floating_days_in_request
            else:
                # Use remaining floating holidays and count extra as leave days
                employee.floating_holidays_used += remaining_floating_balance
                leave_days += (floating_days_in_request - remaining_floating_balance)

        # Ensure the employee has enough leave balance
        if employee.emp_used_leaves + leave_days > employee.emp_total_leaves:
            messages.error(request, "Not enough leave balance!")
            return render(request, 'allocate_leave.html', {'employee': employee})

        # Create Leave Request
        LeaveRequest.objects.create(
            employee_user=employee.user,
            employee_master=employee,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            leave_type="Manager Allocated",
            status="Approved"
        )

        # Update employee leave balance
        employee.emp_used_leaves += leave_days
        employee.save()

        # Send email notification
        send_mail(
            subject="Leave Allocation Notification",
            message=f"Dear {employee.emp_fname},\n\nYour manager {manager.emp_fname} {manager.emp_lname} has allocated leave for you from {start_date} to {end_date}.\n\nReason: {reason}.\n\nBest regards,\nHR Team",
            from_email="ajaykmani2001@gmail.com",
            recipient_list=[employee.emp_email],
            fail_silently=False,
        )

        messages.success(request, f"Leave has been allocated to {employee.emp_fname} {employee.emp_lname}.")
        return redirect('view_subordinates')

    return render(request, 'allocate_leave.html', {
        'employee': employee,
        'emp_id': manager.emp_id,
        'emp_fname': manager.emp_fname,
        'emp_lname': manager.emp_lname,
        'emp_designation': manager.designation,
        'total_used_leaves': total_used_leaves,
        'is_manager': is_manager
    })


def navbar(request):
    return render(request,'admin_partials/admin_header.html')


def sidebar(request):
    return render(request,'admin_partials/admin_left-sidebar.html')


def base(request):
    return render(request , 'admin_partials/admin_base.html')


def parent_view(request):
    return render(request,'partials/base.html')