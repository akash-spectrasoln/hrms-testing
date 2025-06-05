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
from django.conf import settings
from django.utils import timezone
from django.forms import formset_factory
from django.db.models import Max,Min
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from functools import wraps
from django.utils import timezone
import datetime
from django.db import IntegrityError
import time
TIMEOUT_DURATION = 60 * 60  # 60 minutes

def signin_required(fn):
    @wraps(fn)
    def wrapper(request, *args, **kwargs):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return redirect("login")
        
        # Check if the session has timed out due to inactivity
        current_time = time.time()
        last_activity = request.session.get('last_activity', current_time)

        if current_time - last_activity > TIMEOUT_DURATION:
            # If the session expired due to inactivity, log the user out
            logout(request)
            return redirect("login")  # Redirect to sign-in page

        # Update the session's last activity timestamp
        request.session['last_activity'] = current_time

        # Proceed with the original view function
        return fn(request, *args, **kwargs)

    return wrapper


from django.contrib.auth import authenticate, login
from django.contrib import messages
import requests

def employee_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')  # emp_email
        password = request.POST.get('password')

        recaptcha_response = request.POST.get('g-recaptcha-response')  # Get captcha token from frontend

        #  Verify reCAPTCHA with Google
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()

        if not result.get('success'):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return redirect('admin_login')


        # Authenticate with email as the username
        user = authenticate(request, username=email, password=password)
        print(user)
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
from .forms import CustomPasswordChangeForm
from .models import Employees  # Import your Employees model

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
@signin_required
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
        'emp_designation': employee.role.role_name  ,# Employee designation
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



from django.shortcuts import render, get_object_or_404
from .models import Employees


from django.utils.timezone import now
from datetime import date, timedelta
@signin_required
def employee_profile(request, employee_id):
    employee = get_object_or_404(Employees, pk=employee_id, is_deleted=False)
    today = now().date()

    emp_country = employee.country if employee.country else None

    # Financial year calculation
    current_year = today.year
    fin_year_start = date(current_year, 1, 1)
    fin_year_end = date(current_year, 12, 31)

    if emp_country:
        reset_period = HolidayResetPeriod.objects.filter(country=emp_country).first()
        if reset_period:
            start_month = reset_period.start_month
            start_day = reset_period.start_day
            cand_start_date = date(current_year, start_month, start_day)
            if today < cand_start_date:
                fin_year_start = date(current_year - 1, start_month, start_day)
            else:
                fin_year_start = cand_start_date
            try:
                next_fin_year_start = fin_year_start.replace(year=fin_year_start.year + 1)
            except ValueError:
                next_fin_year_start = fin_year_start + timedelta(days=365)
            fin_year_end = next_fin_year_start - timedelta(days=1)

    # Experience calculation (defaults to 0)
    experience_years = (today - employee.created_on.date()).days // 365 if employee.created_on else 0

    # Get leave policies
    policy = HolidayPolicy.objects.filter(
        country=employee.country,
        year=fin_year_start.year,
        min_years_experience__lte=experience_years,
    ).order_by('-min_years_experience').first()
    floating_policy = FloatingHolidayPolicy.objects.filter(
        country=employee.country,
        year=fin_year_start.year
    ).first()
    print(floating_policy)

    # Holidays (used for counting leave days)
    holidays = set(Holiday.objects.filter(
        country=employee.country,
        date__range=(fin_year_start, fin_year_end)
    ).values_list('date', flat=True))

    # All the employee's leaves in this FY
    leaves_qs = LeaveRequest.objects.filter(
        employee_master=employee,
        start_date__lte=fin_year_end,
        end_date__gte=fin_year_start
    )

    def overlapping_leave_days(start_date, end_date, fy_start, fy_end, skip_holidays=None):
        if not start_date or not end_date:
            return 0
        start = max(start_date, fy_start)
        end = min(end_date, fy_end)
        days = 0
        d = start
        while d <= end:
            if d.weekday() < 5:  # Monday-Friday
                if not skip_holidays or d not in skip_holidays:
                    days += 1
            d += timedelta(days=1)
        return days if days > 0 else 0

    # For each leave, subtract used/planned from the available quota (sum types if needed)
    used_leaves = 0
    planned_leaves = 0

    for leave in leaves_qs:
        # Determine total leaves for this type
        leave_type_lower = leave.leave_type.lower()
        if leave_type_lower == "ordinary":
            total_leaves_type = policy.ordinary_holidays_count if policy else 0
        elif leave_type_lower == "casual leave":
            total_leaves_type = (
                (policy.ordinary_holidays_count if policy else 0) +
                (policy.extra_holidays if policy else 0)
            )
        elif leave_type_lower == "floating leave":
            total_leaves_type = floating_policy.allowed_floating_holidays if floating_policy else 0
        else:
            total_leaves_type = 0

        days = overlapping_leave_days(
            leave.start_date, leave.end_date, fin_year_start, fin_year_end, holidays
        )

        if leave.status in ['Accepted', 'Approved'] and leave.end_date < today:
            used_leaves += days
        elif leave.status in ['Accepted', 'Approved'] and leave.end_date >= today:
            planned_leaves += days

    # Here you can sum the policies for a total quota, or decide on a per-type basis.
    # For total (ordinary + casual + floating):
    print(floating_policy.allowed_floating_holidays)
    quota = (policy.ordinary_holidays_count if policy else 0) \
            + (policy.extra_holidays if policy else 0) \
            + (floating_policy.allowed_floating_holidays if floating_policy else 0)
    print(quota)
    print(used_leaves)
    print(planned_leaves)
    available_leaves = max(0, quota - used_leaves - planned_leaves)
    print(available_leaves)
    is_manager = Employees.objects.filter(manager=employee, is_deleted=False).exists()

    return render(request, 'profile.html', {
        'employee': employee,
        'is_manager': is_manager,
        'available_leaves': available_leaves,  # <--- ONLY this number!
    })


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

@signin_required
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
        'employee':employee,
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

@signin_required
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
        'employee':employee,
        'form': form,
        'is_manager': is_manager,
        'emp_id': employee.employee_id,  # Employee ID
        'emp_fname': employee.first_name,  # Employee first name
        'emp_lname': employee.last_name,  # Employee last name
        'emp_designation': employee.role.role_name,  # Employee designation
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

from datetime import timedelta, date, datetime
from django.db.models import Sum, F
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def calculate_working_days(start_date, end_date, holidays, approved_dates):
    working_days = 0
    current_date = start_date
    while current_date <= end_date:
        if (current_date.weekday() not in [5, 6] and  # Exclude Saturday (5) and Sunday (6)
            current_date not in holidays and
            current_date not in approved_dates):
            working_days += 1
        current_date += timedelta(days=1)
    return working_days
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required


def emp_logout(request):
    logout(request)  # Logs out the admin user
    return redirect('login')  # Redirect to the admin login page after logout


from django.core.mail import send_mail
from django.conf import settings
from datetime import date, timedelta
from django.urls import reverse

@signin_required
def get_financial_year_dates(request,employee, reference_date=None):
    """
    Calculate financial year start and end based on employee's country reset period.
    Defaults to calendar year if reset period not set.
    """
    if reference_date is None:
        reference_date = date.today()

    current_year = reference_date.year
    try:
        reset_period = HolidayResetPeriod.objects.get(country=employee.country)
        start_month = reset_period.start_month
        start_day = reset_period.start_day

        fy_start_candidate = date(current_year, start_month, start_day)
        if reference_date < fy_start_candidate:
            fy_start = date(current_year - 1, start_month, start_day)
        else:
            fy_start = fy_start_candidate

        # Financial year end is day before next financial year start
        try:
            fy_end = fy_start.replace(year=fy_start.year + 1) - timedelta(days=1)
        except ValueError:
            # Handle leap-year edge cases by adding 365 days minus 1
            fy_end = fy_start + timedelta(days=365) - timedelta(days=1)

        return fy_start, fy_end

    except HolidayResetPeriod.DoesNotExist:
        # Fallback to calendar year
        return date(current_year, 1, 1), date(current_year, 12, 31)


def overlapping_leave_days(leave_start, leave_end, fy_start, fy_end, holidays=None):
    """
    Calculate number of working days overlap between leave request and financial year period.
    Excludes weekends and specified holidays.
    
    :param leave_start: Leave request start date
    :param leave_end: Leave request end date
    :param fy_start: Financial year start date
    :param fy_end: Financial year end date
    :param holidays: Set or list of holiday dates to exclude
    :return: Number of working days overlapping financial year
    """
    if holidays is None:
        holidays = set()

    start = max(leave_start, fy_start)
    end = min(leave_end, fy_end)

    if end < start:
        return 0

    total_days = 0
    current_day = start
    while current_day <= end:
        # Count only if weekday (Mon=0 to Fri=4) and not a holiday
        if current_day.weekday() < 5 and current_day not in holidays:
            total_days += 1
        current_day += timedelta(days=0)

    return total_days


def leave_days_agg_request(leave_qs, fy_start, fy_end, holidays=None):
    """
    Aggregate working leave days overlapping the financial year,
    considering weekends and holidays.
    
    :param leave_qs: queryset of LeaveRequest to aggregate
    :param fy_start: financial year start date
    :param fy_end: financial year end date
    :param holidays: set or list of holidays (date objects) to exclude from count
    """
    if holidays is None:
        holidays = set()

    total_days = 0
    for leave in leave_qs:
        total_days += overlapping_leave_days(leave.start_date, leave.end_date, fy_start, fy_end, holidays)

    return total_days

@signin_required
def request_leave(request):
    print("hi")
    approval_path = reverse('login')
    approval_url = request.build_absolute_uri(approval_path)

    # Helper to wrap Employee fetch
    def get_employee_and_policy(request_user):
        try:
            employee = Employees.objects.select_related('country', 'manager').get(user_id=request_user.id)
        except Employees.DoesNotExist:
            return None, None, None, None, None
        fy_start, fy_end = get_financial_year_dates(request, employee)
        today = date.today()
        experience_years = (today - employee.created_on.date()).days // 365 if employee.created_on else 0
        reference_year = fy_start.year
        # Only 1 query for policy and 1 for floating
        policy = HolidayPolicy.objects.filter(
            country=employee.country,
            year=reference_year,
            min_years_experience__lte=experience_years
        ).order_by('-min_years_experience').first()
        floating_policy = FloatingHolidayPolicy.objects.filter(
            country=employee.country,
            year=reference_year
        ).first()
        return employee, fy_start, fy_end, policy, floating_policy

    # Helper: get all holidays as sets (avoids repeat queries)
    def get_holidays(employee, fy_start, fy_end):
        holidays = set(
            Holiday.objects.filter(
                country=employee.country,
                date__range=(fy_start, fy_end)
            ).values_list('date', flat=True)
        )
        floating = set(
            FloatingHoliday.objects.filter(
                country=employee.country,
                date__range=(fy_start, fy_end)
            ).values_list('date', flat=True)
        )
        return holidays, floating

    # Helper for aggregation: get all leaves in a date range with one query
    def get_leave_requests(user, fy_start, fy_end):
        return list(LeaveRequest.objects.filter(
            employee_user=user,
            start_date__lte=fy_end,
            end_date__gte=fy_start,
        ).values('leave_type', 'status', 'start_date', 'end_date'))

    # Dates iterator, non-inclusive end
    def daterange(start, end):
        for n in range((end - start).days + 1):
            yield start + timedelta(n)

    # For aggregation, minimize ORM calls
    def agg_leave_days(leaves, target_type, target_statuses, fy_start, fy_end, holidays):
        total = 0
        for lr in leaves:
            if lr['leave_type'] == target_type and lr['status'] in target_statuses:
                for d in daterange(max(lr['start_date'], fy_start), min(lr['end_date'], fy_end)):
                    if d.weekday() < 5 and d not in holidays:
                        total += 1
        return total

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, user=request.user)
        if form.is_valid():
            leave_request = form.save(commit=False)
            info = get_employee_and_policy(request.user)
            if info[0] is None:
                return render(request, 'employee_app/error.html', {'message': 'Employee details not found.'})

            employee, fy_start, fy_end, policy, floating_policy = info
            leave_request.employee_user = request.user
            leave_request.employee_master = employee

            day_type = request.POST.get('day_type')
            if day_type == 'one':
                leave_request.end_date = leave_request.start_date
            else:
                if not leave_request.end_date or leave_request.end_date < leave_request.start_date:
                    messages.error(request, "Please select a valid End Date.")
                    return redirect('request_leave')
            
            holidays, floating_holidays = get_holidays(employee, fy_start, fy_end)
            # Pre-batch all leaves once
            all_leaves = get_leave_requests(request.user, fy_start, fy_end)
            used_casual_leaves = agg_leave_days(all_leaves, "Casual Leave", ['Approved'], fy_start, fy_end, holidays)
            used_floating_leaves = agg_leave_days(all_leaves, "Floating Leave", ['Approved'], fy_start, fy_end, holidays)
            pending_casual_leaves = agg_leave_days(all_leaves, "Casual Leave", ['Pending'], fy_start, fy_end, holidays)
            pending_floating_leaves = agg_leave_days(all_leaves, "Floating Leave", ['Pending'], fy_start, fy_end, holidays)

            casual_leaves = (policy.ordinary_holidays_count if policy else 0) + (policy.extra_holidays if policy else 0)
            floating_leaves = floating_policy.allowed_floating_holidays if floating_policy else 0
            remaining_casual_leaves = (casual_leaves or 0) - (used_casual_leaves or 0) - (pending_casual_leaves or 0)
            remaining_floating_leaves = (floating_leaves or 0) - (used_floating_leaves or 0) - (pending_floating_leaves or 0)
            leave_type = request.POST.get('leave_type')
            original_leave_type = leave_type

            # Precompute sets only once
            all_pending_approved_dates = set(
                d for lr in all_leaves
                if lr['status'] in ['Pending', 'Approved']
                for d in daterange(lr['start_date'], lr['end_date'])
            )

            requested_leave_dates = set(d for d in daterange(leave_request.start_date, leave_request.end_date))
            floating_holidays_in_range = [d for d in requested_leave_dates if d in floating_holidays]
            already_applied = [d for d in floating_holidays_in_range if d in all_pending_approved_dates]
            floating_holiday_confirmed = request.POST.get('floating_holiday_confirmed') == 'true'
            converted_to_casual = False
            if floating_holiday_confirmed or (
                leave_type == "Floating Leave" and used_floating_leaves + len(floating_holidays_in_range) > floating_leaves
            ):
                leave_type = "Casual Leave"
                converted_to_casual = True
                messages.info(request, 'Floating holidays in your range converted to casual leave or exceeded entitlement.')
            if already_applied:
                messages.error(request, f"Leave already applied for floating holiday(s): {', '.join(d.strftime('%Y-%m-%d') for d in already_applied)}")
                return redirect('request_leave')
            if original_leave_type == "Floating Leave" and not converted_to_casual:
                invalid_dates = [d for d in requested_leave_dates if d not in floating_holidays]
                if invalid_dates:
                    formatted_dates = ", ".join(d.strftime('%Y-%m-%d') for d in invalid_dates)
                    messages.error(
                        request,
                        f"Invalid Floating Leave request. The following date(s) are not assigned as floating holidays: {formatted_dates}."
                    )
                    return redirect('request_leave')
                if used_floating_leaves + len(requested_leave_dates) > floating_leaves:
                    messages.error(request, 'Floating holiday limit exceeded; request will be converted to casual leave on next try.')
                    return redirect('request_leave')
                leave_duration = len(requested_leave_dates)
            else:
                # Calculate leave duration considering weekends and holidays
                if converted_to_casual:
                    leave_duration = sum(
                        1 for d in requested_leave_dates
                        if d.weekday() < 5 and d not in holidays and d not in all_pending_approved_dates
                    )
                else:
                    all_holidays = holidays.union(floating_holidays)
                    leave_duration = sum(
                        1 for d in requested_leave_dates
                        if d.weekday() < 5 and d not in all_holidays and d not in all_pending_approved_dates
                    )
            if leave_type == 'Casual Leave' and used_casual_leaves + leave_duration + pending_casual_leaves > casual_leaves:
                messages.error(request, f"Requested Casual Leave exceeds remaining balance ({remaining_casual_leaves} left).")
                return redirect('request_leave')
            if leave_type == 'Floating Leave' and used_floating_leaves + leave_duration + pending_floating_leaves > floating_leaves:
                messages.error(request, "Floating holiday limit exceeded; request will be converted to casual leave.")
                return redirect('request_leave')
            leave_request.leave_type = leave_type
            leave_request.status = 'Pending'
            leave_request.leave_days = leave_duration
            leave_request.created_by = request.user
            leave_request.save()

            manager = getattr(employee, 'manager', None)
            send_mail(
                subject="Leave Request Submitted",
                message=(
                    f"Dear {employee.first_name},\n\nYour leave request ({leave_request.leave_type}) "
                    f"from {leave_request.start_date} to {leave_request.end_date} has been submitted and is pending approval.\n\n"
                    "Best regards,\nHR Team"
                ),
                from_email="lms@spectrasoln.com",
                recipient_list=[employee.company_email],
                fail_silently=False,
            )
            if manager and getattr(manager, 'company_email', None):
                send_mail(
                    subject="Leave Approval Required",
                    message = (
                                f"Dear {manager.first_name},\n\n"
                                f"Employee {employee.first_name} {employee.last_name} "
                                f"has requested leave ({leave_request.leave_type}) from {leave_request.start_date} "
                                f"to {leave_request.end_date}. Please review the request in the HR system.\n\n"
                                f"Login here: {approval_url}\n\n"
                                f"Best regards,\nHR Team"
                            ),
                    from_email="lms@spectrasoln.com",
                    recipient_list=[manager.company_email],
                    fail_silently=False,
                )
            messages.success(request, "Leave request submitted successfully.")
            return redirect('request_leave')

    else:
        form = LeaveRequestForm(user=request.user)
        try:
            employee = Employees.objects.select_related('country', 'manager').get(company_email=request.user.email)
        except Employees.DoesNotExist:
            return render(request, 'employee_app/error.html', {'message': 'Employee details not found.'})
        is_manager = Employees.objects.filter(manager=employee).exists()
        today = date.today()
        experience_years = (today - employee.created_on.date()).days // 365 if employee.created_on else 0
        fy_start, fy_end = get_financial_year_dates(request, employee)
        policy = HolidayPolicy.objects.filter(
            country=employee.country,
            year=fy_start.year,
            min_years_experience__lte=experience_years
        ).order_by('-min_years_experience').first()
        floating_policy = FloatingHolidayPolicy.objects.filter(
            country=employee.country,
            year=fy_start.year
        ).first()
        casual_leaves = (policy.ordinary_holidays_count if policy else 0) + (policy.extra_holidays if policy else 0)
        floating_leaves = floating_policy.allowed_floating_holidays if floating_policy else 0
        holidays, floating_holidays = get_holidays(employee, fy_start, fy_end)

        # Only call DB for all leaves ONCE!
        all_leaves = get_leave_requests(request.user, fy_start, fy_end)
        used_casual_leaves = agg_leave_days(all_leaves, "Casual Leave", ['Approved'], fy_start, fy_end, holidays)
        used_floating_leaves = agg_leave_days(all_leaves, "Floating Leave", ['Approved'], fy_start, fy_end, holidays)
        used_pending_casual_leaves = agg_leave_days(all_leaves, "Casual Leave", ['Pending'], fy_start, fy_end, holidays)
        used_pending_floating_leaves = agg_leave_days(all_leaves, "Floating Leave", ['Pending'], fy_start, fy_end, holidays)
        remaining_casual_leaves = (casual_leaves or 0) - (used_casual_leaves or 0) - (used_pending_casual_leaves or 0)
        remaining_floating_leaves = (floating_leaves or 0) - (used_floating_leaves or 0) - (used_pending_floating_leaves or 0)
        # All leave dates (reduce ORM hits)
        approved_leave_dates = [
            d.strftime('%Y-%m-%d')
            for lr in all_leaves if lr['status'] == 'Approved'
            for d in daterange(lr['start_date'], lr['end_date'])
        ]
        pending_leave_dates = [
            d.strftime('%Y-%m-%d')
            for lr in all_leaves if lr['status'] == 'Pending'
            for d in daterange(lr['start_date'], lr['end_date'])
        ]
        weekends = []
        current_month = today.month
        day = date(today.year, current_month, 1)
        while day.month == current_month:
            if day.weekday() in [5, 6]:  # Saturday=5, Sunday=6
                weekends.append(day.strftime('%Y-%m-%d'))
            day += timedelta(days=1)

        context = {
            'employee': employee,
            'form': form,
            'employee_name': f"{employee.first_name} {employee.last_name}",
            'employee_email': employee.company_email,
            'holidays': [d.strftime('%Y-%m-%d') for d in holidays],
            'floating_holidays': [d.strftime('%Y-%m-%d') for d in floating_holidays],
            'weekends': weekends,
            'approved_leave_dates': approved_leave_dates,
            'pending_leave_dates': pending_leave_dates,
            'is_manager': is_manager,
            'emp_designation': employee.role.role_name,
            'emp_id': employee.employee_id,
            'emp_fname': employee.first_name,
            'emp_lname': employee.last_name,
            'casual_leaves': casual_leaves,
            'floating_leaves': floating_leaves,
            'used_casual_leaves': used_casual_leaves,
            'used_floating_leaves': used_floating_leaves,
            'used_pending_casual_leaves': used_pending_casual_leaves,
            'used_pending_floating_leaves': used_pending_floating_leaves,
            'remaining_casual_leaves': remaining_casual_leaves,
            'remaining_floating_leaves': remaining_floating_leaves,
        }
        return render(request, 'leaverequest.html', context)

from django.core.mail import send_mail
from django.http import HttpResponse

def test_email(request):
    try:
        send_mail(
            subject='Test Email',
            message='This is a test email from Django.',
            from_email='lms@spectrasoln.com',
            recipient_list=['akashaku32@gmail.com'],  # Add a valid recipient email
            fail_silently=False,  # Set to False to catch exceptions
        )
        return HttpResponse('Email sent successfully.')
    except Exception as e:
        return HttpResponse(f'Error occurred: {e}')
@signin_required
def check_floating_holidays(request):
    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # Fetch floating holidays
        current_year = date.today().year
        floating_holidays = list(FloatingHoliday.objects.filter(date__year=current_year).values_list('date', flat=True))

        # Fetch all leave dates for the employee (any status)
        all_leave_dates = set(
            d for start, end in LeaveRequest.objects.filter(
                employee_user=request.user
            ).values_list('start_date', 'end_date')
            for d in daterange(start, end)
        )

        floating_holiday_status = []
        for holiday in floating_holidays:
            if start_date <= holiday <= end_date:
                status = "applied" if holiday in all_leave_dates else "not_applied"
                floating_holiday_status.append({
                    "date": holiday.strftime('%Y-%m-%d'),
                    "status": status
                })

        return JsonResponse({
            'floating_holiday_status': floating_holiday_status
        })
# view for debugging
@signin_required
def check_leave_conflicts(request):
    print("he")
    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # Fetch employee profile and country
        employee_profile = Employees.objects.get(user=request.user)
        if not employee_profile:
            return JsonResponse({'error': 'Employee profile not found'}, status=400)
        country = employee_profile.country

        # Determine financial year range based on leave start date and country
        fy_start_date, fy_end_date = get_financial_year_dates(request, employee_profile)

        # Filter leaves for the user within financial year and status Pending or Approved
        leave_qs = LeaveRequest.objects.filter(
            employee_user=request.user,
            status__in=['Pending', 'Approved'],
            start_date__lte=fy_end_date,
            end_date__gte=fy_start_date,
        )

        # Collect all leave dates that overlap with the requested leave range
        leave_dates = set()
        for leave_start, leave_end in leave_qs.values_list('start_date', 'end_date'):
            # Calculate intersection with selected leave range to avoid dates outside that range
            overlap_start = max(leave_start, start_date)
            overlap_end = min(leave_end, end_date)
            if overlap_start <= overlap_end:
                leave_dates.update(daterange(overlap_start, overlap_end))

        # Floating holidays for the employee's country within financial year
        floating_holidays = set(FloatingHoliday.objects.filter(
            country=country,
            date__gte=fy_start_date,
            date__lte=fy_end_date
        ).values_list('date', flat=True))

        # Dates requested by user
        selected_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

        # Conflicts: selected dates that are already applied leaves (pending or approved)
        conflict_dates = [d.strftime('%Y-%m-%d') for d in selected_dates if d in leave_dates]

        # Floating holidays in the selected range not yet applied for
        floating_holiday_not_applied = [
            d.strftime('%Y-%m-%d') for d in selected_dates if d in floating_holidays and d not in leave_dates
        ]
        
        print(floating_holiday_not_applied)
        return JsonResponse({
            'conflict_dates': conflict_dates,
            'floating_holiday_not_applied': floating_holiday_not_applied
        })
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


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import LeaveRequest

def delete_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, pk=leave_id, employee_user=request.user)
    employee = leave.employee_master
    if request.method == "POST":
        if leave.status in ["Accepted", "Approved"]:
            if leave.leave_type == "Floating Leave":
                employee.floating_holidays_used = max(0, employee.floating_holidays_used - (leave.leave_days or 0))
            else:  # For "Casual Leave", "Sick Leave", etc.
                employee.used_leaves = max(0, employee.used_leaves - (leave.leave_days or 0))
            employee.save()
        
        # Soft delete
        leave.status = 'Deleted'
        leave.approved_by = leave.employee_user
        leave.save()
        
        messages.success(request, "Planned leave deleted successfully.")
    else:
        messages.error(request, "Invalid delete operation.")
    return redirect('my_leave_history')# Make sure this name matches your leave history view name

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import LeaveRequest,HolidayPolicy,FloatingHolidayPolicy
from django.db.models import Sum, Q
from django.utils.timezone import now



from django.shortcuts import render
from django.db.models import Q, Sum
from django.utils.timezone import now
from datetime import date, datetime, timedelta
from .models import Employees, LeaveRequest, HolidayPolicy, FloatingHolidayPolicy, HolidayResetPeriod
@signin_required

def my_leave_history(request):
    user = request.user
    today = now().date()

    # Fetch employee and country efficiently
    employee = Employees.objects.select_related('country').filter(user=user).first()
    emp_country = employee.country if employee else None

    current_year = today.year
    fin_year_start = date(current_year, 1, 1)
    fin_year_end = date(current_year, 12, 31)

    # Override financial year from HolidayResetPeriod, if defined
    if emp_country:
        reset_period = HolidayResetPeriod.objects.filter(country=emp_country).first()
        if reset_period:
            start_month = reset_period.start_month
            start_day = reset_period.start_day
            cand_start_date = date(current_year, start_month, start_day)
            if today < cand_start_date:
                fin_year_start = date(current_year - 1, start_month, start_day)
            else:
                fin_year_start = cand_start_date
            try:
                next_fin_year_start = fin_year_start.replace(year=fin_year_start.year + 1)
            except ValueError:
                next_fin_year_start = fin_year_start + timedelta(days=365)
            fin_year_end = next_fin_year_start - timedelta(days=1)

    validity_range = f"{fin_year_start.strftime('%b %d, %Y')} - {fin_year_end.strftime('%b %d, %Y')}"

    status_filter = request.GET.get('status', '').lower()

    # Batch fetch all leave requests for the user, for this year (use select_related for related access in template)
    leave_requests_qs = LeaveRequest.objects.filter(employee_user=user).select_related('employee_master').order_by('-start_date')

    # Apply status filter if provided
    if status_filter == 'pending':
        leave_requests_qs = leave_requests_qs.filter(status__iexact='Pending')
    elif status_filter == 'upcoming':
        leave_requests_qs = leave_requests_qs.filter(status__in=['Accepted', 'Approved'], end_date__gte=today)
    elif status_filter == 'approved':
        leave_requests_qs = leave_requests_qs.filter(status__in=['Accepted', 'Approved'])
    elif status_filter == 'rejected':
        leave_requests_qs = leave_requests_qs.filter(status__iexact='Rejected')
    elif status_filter == 'deleted':
        leave_requests_qs = leave_requests_qs.filter(status__iexact='Deleted')

    leave_requests = list(leave_requests_qs)

    # Assign status flags for all at once
    for leave in leave_requests:
        leave.is_pending = (leave.status == 'Pending')
        leave.is_approved = (leave.status in ['Accepted', 'Approved'])
        leave.is_rejected = (leave.status == 'Rejected')
        leave.is_deleted = (leave.status == 'Deleted')

    # Is manager & experience years
    is_manager = getattr(employee, 'employees_managed', Employees.objects.none()).exists() if employee else False
    experience_years = (today - employee.created_on.date()).days // 365 if employee and employee.created_on else 0

    # Batch get policies and all holidays, reusing them
    policy = None
    floating_policy = None
    holidays = []
    floating_holidays = []
    print(experience_years)
    print(fin_year_start.year)
    print(employee.country)
    if employee:
        policy = HolidayPolicy.objects.filter(
            country=employee.country,
            year=fin_year_start.year,  # use adjusted financial year
            min_years_experience__lte=experience_years,
        ).order_by('-min_years_experience').first()
        print(policy)
        floating_policy = FloatingHolidayPolicy.objects.filter(
            country=employee.country,
            year=fin_year_start.year
        ).first()

        holidays = list(
            Holiday.objects.filter(
                country=employee.country,
                date__range=(fin_year_start, fin_year_end)
            ).values_list('date', flat=True)
        )
        floating_holidays = list(
            FloatingHoliday.objects.filter(
                country=employee.country,
                date__range=(fin_year_start, fin_year_end)
            ).values_list('date', flat=True)
        )

    holidays_set = set(holidays)
    floating_holidays_set = set(floating_holidays)

    # --- PRELOAD all relevant leaves for the financial year (used in *all* stats) ---
    leaves_qs = LeaveRequest.objects.filter(
        employee_master=employee,
        start_date__lte=fin_year_end,
        end_date__gte=fin_year_start
    ).only("leave_type", "status", "start_date", "end_date")

    # Pre-slice all leaves into buckets for fast sum in the summary
    leaves_by_type = {k: [] for k, _ in LeaveRequest.LEAVE_TYPES}
    for leave in leaves_qs:
        leaves_by_type.setdefault(leave.leave_type, []).append(leave)

    # Helper: count overlap days, skipping holidays if required
    def overlapping_leave_days(start_date, end_date, fy_start, fy_end, skip_holidays=None):
        if not start_date or not end_date:
            return 0
        start = max(start_date, fy_start)
        end = min(end_date, fy_end)
        days = 0
        d = start
        while d <= end:
            if d.weekday() < 5:  # Monday-Friday are 0-4
                if not skip_holidays or d not in skip_holidays:
                    days += 1
            d += timedelta(days=1)
        return days if days > 0 else 0

    leave_summary_data = []

    for leave_type, description in LeaveRequest.LEAVE_TYPES:
        # get all leaves of this type (for summary)
        lvs = leaves_by_type.get(leave_type, [])
        # Fetch total allowed leaves efficiently
        leave_type_lower = leave_type.lower()
        if leave_type_lower == "ordinary":
            total_leaves = policy.ordinary_holidays_count if policy else 0
        elif leave_type_lower == "casual leave":
            total_leaves = (
                (policy.ordinary_holidays_count if policy else 0) +
                (policy.extra_holidays if policy else 0)
            )
        elif leave_type_lower == "floating leave":
            total_leaves = floating_policy.allowed_floating_holidays if floating_policy else 0
        else:
            total_leaves = 0
        # Used, planned, pending leaves. Python filter for in-memory efficiency
        used_leaves = sum(
            overlapping_leave_days(l.start_date, l.end_date, fin_year_start, fin_year_end, holidays_set)
            for l in lvs if l.status in ['Accepted', 'Approved'] and l.end_date < today
        )
        planned_leaves = sum(
            overlapping_leave_days(l.start_date, l.end_date, fin_year_start, fin_year_end, holidays_set)
            for l in lvs if l.status in ['Accepted', 'Approved'] and l.end_date >= today
        )
        pending_leaves = sum(
            overlapping_leave_days(l.start_date, l.end_date, fin_year_start, fin_year_end, holidays_set)
            for l in lvs if l.status.lower() == 'pending' and l.end_date >= today
        )
        leave_summary_data.append({
            'leave_type': description,
            'validity': validity_range,
            'total': total_leaves,
            'used': used_leaves,
            'planned': planned_leaves,
            'pending': pending_leaves,
            'available': max(0, total_leaves - used_leaves - planned_leaves),
        })
    print(total_leaves)
    total_used_leaves = sum(item['used'] for item in leave_summary_data)

    planned_leave_requests = LeaveRequest.objects.filter(
        employee_user=user,
        status__in=["Accepted", "Approved"],
        start_date__lte=fin_year_end,
        end_date__gte=today,
    ).order_by('start_date')

    context = {
        'employee': employee,
        'leave_requests': leave_requests,
        'leave_summary': leave_summary_data,
        'is_manager': is_manager,
        'emp_designation': employee.role.role_name if employee else '',
        'emp_id': employee.employee_id if employee else '',
        'emp_fname': employee.first_name if employee else '',
        'emp_lname': employee.last_name if employee else '',
        'total_used_leaves': total_used_leaves,
        'planned_leave_requests': planned_leave_requests,
        'request': request,
        'today': today,
        'financial_year_start': fin_year_start,
        'financial_year_end': fin_year_end,
        'financial_year_range_display': validity_range,
    }

    return render(request, 'my_leave_history.html', context)


from django.utils.timezone import now
@signin_required
def emp_index(request):
    try:
        employee = Employees.objects.get(company_email=request.user.username)
    except Employees.DoesNotExist:
        return render(request, 'error.html', {'message': 'Employee not found.'})

    # Check if the employee is a manager (has subordinates)
    if employee.employees_managed.exists():  # If there are employees managed by this employee
        is_manager = True
    else:
        is_manager = False

    # Get total used leaves for the current year
    current_year = now().year  # Get current year
    total_used_leaves = employee.used_leaves  # Fetch from the Employees model

    return render(request, 'emp_index.html', {
        'employee': employee,
        'is_manager': is_manager , # Pass whether the employee is a manager or not
        'total_used_leaves': total_used_leaves , # Pass the used leaves count to the template
        'emp_designation': employee.role.role_name,  # Employee designation
        'emp_id': employee.employee_id,  # Employee ID
        'emp_fname' : employee.first_name, #employee firstname
        'emp_lname' : employee.last_name #employee lastname
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

@signin_required
def total_leaves_view(request):
    user = request.user
    # Fetch the related Employees object
    employee = get_object_or_404(Employees, user=user)  # Adjust based on the relationship in Employees

    current_year = date.today().year
    total_leaves = get_total_leaves(employee, year=current_year)

    return render(request, 'total_leaves.html', {'employee':employee,'total_leaves': total_leaves, 'year': current_year})




# to get all the holidays in a year

from django.shortcuts import render
from datetime import date
from .models import Holiday, FloatingHoliday
from datetime import datetime

def holiday_list(request):
    current_year = date.today().year  # Get the current year
    is_manager = False  # Default value
    if request.user.is_authenticated:
        try:
            employee = Employees.objects.get(company_email=request.user.email)
            is_manager = employee.employees_managed.exists()  # Checks if they manage anyone
        except Employees.DoesNotExist:
            pass  # If no employee record is found, keep is_manager as False

    # Filter holidays and floating holidays for the current year
    holidays = Holiday.objects.filter(date__year=current_year,country=employee.country).order_by('date')
    floating_holidays = FloatingHoliday.objects.filter(date__year=current_year,country=employee.country).order_by('date')

    # Check if the logged-in user is a manager
    
    current_year = now().year  # Get current year
    total_used_leaves = employee.used_leaves  # Fetch from the Employees model

    context = {
        'employee':employee,
        'holidays': holidays,
        'floating_holidays': floating_holidays,
        'is_manager': is_manager,  # Pass manager status to template
        'emp_designation': employee.role.role_name,  # Employee designation
        'emp_id': employee.employee_id,  # Employee ID
        'emp_fname': employee.first_name,  # employee firstname
        'emp_lname': employee.last_name , # employee lastname
        'total_used_leaves' : total_used_leaves
    }
    return render(request, 'holiday_list.html', context)









from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from .models import LeaveRequest, Employees
from datetime import datetime
from django.utils.timezone import now


from .models import Employees, LeaveRequest

from django.utils.timezone import now
from django.db.models import Q
@signin_required


def manager_leave_requests(request):
    try:
        employee = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        return render(request, 'employee_app/error.html', {'message': 'Manager profile not found.'})

    # Ensure only managers see this page
    subordinates = Employees.objects.filter(manager=employee)
    if not subordinates.exists():
        return HttpResponse("cannot access")

    is_manager = True

    # Get filter params
    employee_name = request.GET.get('employee_name', '').strip()
    status = request.GET.get('status', '').strip()
    year_str = request.GET.get('year', '').strip()

    # Determine country for financial year calculation (assuming employee.country is Country instance)
    country = employee.country if hasattr(employee, 'country') else None

    # Reference date for financial year calc: mid-year of selected year or today if no year specified
    try:
        year = int(year_str)
        reference_date = date(year, 7, 1)
    except (ValueError, TypeError):
        reference_date = date.today()

    # Financial year start and end — update your get_financial_year_dates to accept country instance
    fy_start, fy_end = get_financial_year_dates(request, employee)

    # Base leave requests filtered by subordinates and financial year overlap
    leave_requests = LeaveRequest.objects.filter(
        employee_master__in=subordinates,
        start_date__lte=fy_end,
        end_date__gte=fy_start,
    )

    # Filter by employee name if provided
    if employee_name:
        leave_requests = leave_requests.filter(
            Q(employee_master__first_name__icontains=employee_name) |
            Q(employee_master__last_name__icontains=employee_name)
        )

    # Filter by status
    if 'status' in request.GET:
        if status != '':
            leave_requests = leave_requests.filter(status__iexact=status)
        # else: empty means show all - no filter
    else:
        status = 'Pending'
        leave_requests = leave_requests.filter(status__iexact=status)

    # Default year for UI dropdown and display
    if not year_str or not year_str.isdigit():
        year_str = str(fy_start.year)

    # Get available years for subordinates’ leaves (using fiscal year start year)
    all_leave_requests = LeaveRequest.objects.filter(employee_master__in=subordinates)
    available_years = sorted(set(
        all_leave_requests.values_list('start_date__year', flat=True)
    ), reverse=True)

    context = {
        'is_manager': is_manager,
        'employee': employee,
        'leave_requests': leave_requests.order_by('-start_date'),
        'available_years': available_years,
        'selected_employee_name': employee_name,
        'selected_status': status,
        'selected_year': year_str,
    }

    return render(request, 'manage_leave_requests.html', context)
@signin_required
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
    leave_requests = LeaveRequest.objects.filter(employee_master__manager=manager)

    # Apply filters
    if year:
        leave_requests = leave_requests.filter(start_date__year=year)

    if employee_name:
        leave_requests = leave_requests.filter(
            Q(employee_master__first_name__icontains=employee_name) |
            Q(employee_master__last_name__icontains=employee_name)
        )

    if status:
        leave_requests = leave_requests.filter(status=status)

    # Prepare filtered data for response
    filtered_data = [
        {
            'id': leave.id,
            'employee_name': f"{leave.employee_master.first_name} {leave.employee_master.last_name}".strip(),
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

from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import LeaveRequest, Employees, Holiday, FloatingHoliday
from django.utils.timezone import now
from datetime import timedelta

@signin_required
def manage_leave_request(request, leave_request_id):
    leave_request = get_object_or_404(LeaveRequest, id=leave_request_id)

    # Ensure the logged-in manager or admin is allowed to act on this leave request
    if not request.user.is_superuser and leave_request.employee_master.manager.user != request.user:
        return render(request, 'employee_app/error.html', {'message': 'Unauthorized action.'})

    try:
        logged_in_employee = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        return render(request, 'employee_app/error.html', {'message': 'Employee profile not found.'})

    is_manager = Employees.objects.filter(manager=logged_in_employee).exists()
    current_year = now().year
    total_used_leaves = logged_in_employee.used_leaves

    if request.method == 'POST':
        action = request.POST.get('action')
        start_date = leave_request.start_date
        end_date = leave_request.end_date
        employee = leave_request.employee_master

        leave_duration = 0
        floating_holidays_used = employee.floating_holidays_used
        max_floating_holidays = employee.floating_holidays_balance+employee.floating_holidays_used

        current_date = start_date
        holidays = set(Holiday.objects.values_list('date', flat=True))
        floating_holidays = set(FloatingHoliday.objects.values_list('date', flat=True))
        while current_date <= end_date:
            if current_date.weekday() in [5, 6]:
                current_date += timedelta(days=1)
                continue
            if current_date in holidays:
                current_date += timedelta(days=1)
                continue
            if current_date in floating_holidays:
                if floating_holidays_used < max_floating_holidays:
                    floating_holidays_used += 1
                    current_date += timedelta(days=1)
                    continue
            leave_duration += 1
            current_date += timedelta(days=1)

        if action == 'accept':
            leave_request.status = 'Approved'
            if employee.used_leaves + leave_duration <= 15:
                employee.used_leaves += leave_duration
                employee.floating_holidays_used = floating_holidays_used
                employee.save()
            else:
                messages.error(request, "Employee cannot exceed the allowed 15 total leave days.")
                return redirect('manager_leave_requests')

            # Email to employee: LEAVE APPROVED
            send_mail(
                subject="Your Leave Request Has Been Approved",
                message=(
                    f"Dear {employee.first_name},\n\n"
                    f"Your leave request from {leave_request.start_date} to {leave_request.end_date} ({leave_request.leave_type}) "
                    "has been approved. Enjoy your time off!\n\n"
                    "Best regards,\nHR Team"
                ),
                from_email="lms@spectrasoln.com",
                recipient_list=[employee.company_email],
                fail_silently=False,
            )

        elif action == 'reject':
            leave_request.status = 'Rejected'

            # Email to employee: LEAVE REJECTED
            send_mail(
                subject="Your Leave Request Has Been Rejected",
                message=(
                    f"Dear {employee.first_name},\n\n"
                    f"Your leave request from {leave_request.start_date} to {leave_request.end_date} ({leave_request.leave_type}) "
                    "has been rejected. For more information, please contact your manager.\n\n"
                    "Best regards,\nHR Team"
                ),
                from_email="lms@spectrasoln.com",
                recipient_list=[employee.company_email],
                fail_silently=False,
            )

        if request.user.is_superuser:
            leave_request.approved_by = request.user
        else:
            
            leave_request.approved_by = request.user

        leave_request.save()
        return redirect('manager_leave_requests')

    return render(
        request,
        'manage_leave_requests.html',
        {
            'employee':employee,
            'leave_request': leave_request,
            'is_manager': is_manager,
            'emp_designation': logged_in_employee.role.role_name,
            'emp_id': logged_in_employee.employee_id,
            'emp_fname': logged_in_employee.first_name,
            'emp_lname': logged_in_employee.last_name,
            'total_used_leaves': total_used_leaves
        }
    )






def test(request):
    return render(request,'test.html')



# 4-2-2025

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Employees

@signin_required
def view_subordinates(request):
    """View to list subordinates of the logged-in manager."""
    try:
        manager = Employees.objects.get(user=request.user)  # Get manager's employee record
    except Employees.DoesNotExist:
        return render(request, 'employee_app/error.html', {'message': 'Employee profile not found.'})

    # Fetch employees who report to this manager
    subordinates = Employees.objects.filter(manager=manager)

    # Check if the logged-in employee is actually a manager
    is_manager = subordinates.exists()  # If they have subordinates, they're a manager

    current_year = now().year  # Get current year
    total_used_leaves = manager.used_leaves  # Fetch from the Employees model

    return render(request, 'view_subordinates.html', {
        'employee':manager,
        'subordinates': subordinates,
        'manager': manager,
        'is_manager' : is_manager,
        'emp_id' : manager.employee_id ,
        'emp_fname' : manager.first_name,
        'emp_lname' : manager.last_name,
        'emp_designation' : manager.role.role_name,
        'total_used_leaves' : total_used_leaves
    })




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Q
from datetime import datetime
from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Q

from .models import Employees, LeaveRequest, Holiday, FloatingHoliday, HolidayPolicy, FloatingHolidayPolicy

def leave_days_agg(queryset):
    # Helper to sum leave_days with fallbacks for missing values
    return sum(lr.leave_days or 0 for lr in queryset)


def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)


from datetime import date, datetime, timedelta
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Sum



@signin_required
def allocate_leave(request, employee_id):
    manager = get_object_or_404(Employees, user=request.user)
    employee = get_object_or_404(Employees, id=employee_id)
    today = date.today()

    current_year = today.year
    subordinates = Employees.objects.filter(manager=manager)
    is_manager = subordinates.exists()

    # Get fixed holidays (exclude floating holidays)
    regular_holidays = set(Holiday.objects.filter(country=employee.country, year=current_year).values_list('date', flat=True))
    floating_holiday_dates = set(FloatingHoliday.objects.filter(country=employee.country, year=current_year).values_list('date', flat=True))

    # Calculate financial year start and end dates
    financial_year_start, financial_year_end = get_financial_year_dates(request, employee, reference_date=today)

    # --- Calculate LEAVE POLICY ---
    experience_years = (today - employee.created_on.date()).days // 365 if employee.created_on else 0

    policy = HolidayPolicy.objects.filter(country=employee.country, year=current_year, min_years_experience__lte=experience_years).order_by('-min_years_experience').first()
    floating_policy = FloatingHolidayPolicy.objects.filter(country=employee.country, year=current_year).first()
    casual_leaves = (policy.ordinary_holidays_count if policy else 0) + (policy.extra_holidays if policy else 0)
    floating_leaves = floating_policy.allowed_floating_holidays if floating_policy else 0
    print(casual_leaves)
    print(floating_leaves)
    def leave_days_agg(qs):
        agg = qs.aggregate(total=Sum('leave_days'))
        return agg['total'] or 0

    # --- Calculate used and pending leaves BASED ON FINANCIAL YEAR ---
    used_casual_leaves = leave_days_agg(LeaveRequest.objects.filter(
        employee_user=employee.user,
        leave_type='Casual Leave',
        status='Approved',
        start_date__lte=financial_year_end,
        end_date__gte=financial_year_start,
    ))
    pending_casual_leaves = leave_days_agg(LeaveRequest.objects.filter(
        employee_user=employee.user,
        leave_type='Casual Leave',
        status='Pending',
        start_date__lte=financial_year_end,
        end_date__gte=financial_year_start,
    ))
    used_floating_leaves = leave_days_agg(LeaveRequest.objects.filter(
        employee_user=employee.user,
        leave_type='Floating Leave',
        status='Approved',
        start_date__lte=financial_year_end,
        end_date__gte=financial_year_start,
    ))
    pending_floating_leaves = leave_days_agg(LeaveRequest.objects.filter(
        employee_user=employee.user,
        leave_type='Floating Leave',
        status='Pending',
        start_date__lte=financial_year_end,
        end_date__gte=financial_year_start,
    ))

    remaining_casual_leaves = casual_leaves - used_casual_leaves - pending_casual_leaves
    print(remaining_casual_leaves)
    remaining_floating_leaves = floating_leaves - used_floating_leaves - pending_floating_leaves
    print(remaining_floating_leaves)

    # --- Financial Year Leave Aggregations ---
    leaves_fin_year = LeaveRequest.objects.filter(
        employee_user=employee.user,
        start_date__lte=financial_year_end,
        end_date__gte=financial_year_start,
    )

    def leave_days_agg_by_status(status_list):
        agg = leaves_fin_year.filter(status__in=status_list).aggregate(total_days=Sum('leave_days'))
        return agg['total_days'] or 0

    approved_leaves = leave_days_agg_by_status(['Approved'])
    pending_leaves = leave_days_agg_by_status(['Pending'])
    rejected_leaves = leave_days_agg_by_status(['Rejected'])

    upcoming_leaves = leaves_fin_year.filter(
        start_date__gte=today,
        status__in=['Pending', 'Accepted', 'Approved']
    ).aggregate(total_days=Sum('leave_days'))['total_days'] or 0

    all_leaves = leaves_fin_year.aggregate(total_days=Sum('leave_days'))['total_days'] or 0

    # --- POST Request Handling ---
    if request.method == "POST":
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")
        reason = request.POST.get("reason", "").strip()
        leave_type = request.POST.get("leave_type", "").strip()

        error = None
        if not start_date_str or not end_date_str:
            error = "Both start and end date are required."
        elif not reason:
            error = "Reason is required."
        elif not leave_type:
            error = "Leave type is required."

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except Exception:
            start_date = None
            end_date = None
            if not error:
                error = "Invalid date format."

        if not error and start_date and end_date and end_date < start_date:
            error = "End date cannot be before start date."

        if not error and start_date and end_date:
            requested_dates = list(daterange(start_date, end_date))
            if leave_type == "Floating Leave":
                leave_days = sum(1 for d in requested_dates if d in floating_holiday_dates)
                invalid_days = [d for d in requested_dates if d not in floating_holiday_dates]
                if invalid_days:
                    error = "Selected dates include days that are not floating holidays."
            else:
                leave_days = sum(1 for d in requested_dates if d.weekday() < 5 and d not in regular_holidays)
            if not error and leave_days <= 0:
                error = "No valid leave days selected (after skipping weekends/fixed holidays)."

        if not error:
            if leave_type == "Floating Leave" and leave_days > remaining_floating_leaves:
                error = f"Not enough floating leave balance! Only {remaining_floating_leaves} left."
            elif leave_type == "Casual Leave" and leave_days > remaining_casual_leaves:
                error = f"Not enough casual leave balance! Only {remaining_casual_leaves} left."

        if not error and start_date and end_date:
            overlapping = LeaveRequest.objects.filter(
                employee_user=employee.user,
                status__in=['Pending', 'Accepted', 'Approved'],
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            if overlapping.exists():
                error = "A leave already exists for the employee overlapping these dates."

        if error:
            messages.error(request, error)
        else:
            LeaveRequest.objects.create(
                employee_user=employee.user,
                employee_master=employee,
                start_date=start_date,
                end_date=end_date,
                reason=f'{reason} (Manager allocated)',
                leave_type=leave_type,
                status="Approved",
                leave_days=leave_days,
                approved_by=request.user,
                created_by=request.user
            )
            if leave_type == "Floating Leave":
                employee.floating_holidays_used += leave_days
            elif leave_type == "Casual Leave":
                employee.used_leaves += leave_days
            employee.save()

            send_mail(
                subject="Leave Allocation Notification",
                message=(
                    f"Dear {employee.first_name},\n\n"
                    f"Your manager {manager.first_name} {manager.last_name} "
                    f"has allocated {leave_type} for you from {start_date} to {end_date}.\n\n"
                    f"Number of days: {leave_days}\n"
                    f"Reason: {reason}\n\n"
                    "Best regards,\nHR Team"
                ),
                from_email="lms@spectrasoln.com",
                recipient_list=[employee.company_email],
                fail_silently=False,
            )

            messages.success(request, f"{leave_type} allocated to {employee.first_name} {employee.last_name}.")
            return redirect('view_subordinates')

    context = {
        'employee': employee,
        'holidays': [d.strftime('%Y-%m-%d') for d in regular_holidays],
        'floating_holidays': [d.strftime('%Y-%m-%d') for d in floating_holiday_dates],
        'remaining_casual_leaves': remaining_casual_leaves,
        'remaining_floating_leaves': remaining_floating_leaves,
        'is_manager': is_manager,

        # Financial year leave aggregates
        'financial_year_start': financial_year_start,
        'financial_year_end': financial_year_end,
        'approved_leaves': approved_leaves,
        'pending_leaves': pending_leaves,
        'rejected_leaves': rejected_leaves,
        'upcoming_leaves': upcoming_leaves,
        'all_leaves': all_leaves,
    }
    return render(request, 'allocate_leave.html', context)
def navbar(request):
    employee=Employees.objects.get(user=request.user)
    context={
        'employee':employee
    }
    return render(request,'admin_partials/admin_header.html',context)


def sidebar(request):
    return render(request,'admin_partials/admin_left-sidebar.html')


def base(request):
    return render(request , 'admin_partials/admin_base.html')


def parent_view(request):
    return render(request,'partials/base.html')