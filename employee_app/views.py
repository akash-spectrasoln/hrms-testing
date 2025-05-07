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

from datetime import timedelta, date, datetime
from django.db.models import Sum, F
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
def leave_days_agg(queryset):
    """
    Aggregates total leave days from LeaveRequest.leave_days
    Returns an integer (handles None values gracefully).
    """
    # Sum the 'leave_days' field directly
    days = queryset.aggregate(total_days=Sum('leave_days'))['total_days']
    return days or 0
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

from django.core.mail import send_mail
from django.conf import settings
from datetime import date, timedelta
@login_required



def request_leave(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, user=request.user)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.employee_user = request.user

            day_type = request.POST.get('day_type')
            if day_type == 'one':
                leave_request.end_date = leave_request.start_date
            else:
                if not leave_request.end_date or leave_request.end_date < leave_request.start_date:
                    messages.error(request, "Please select a valid End Date.")
                    return redirect('request_leave')

            try:
                employee = Employees.objects.get(company_email=request.user.email)
            except Employees.DoesNotExist:
                return render(request, 'employee_app/error.html', {'message': 'Employee details not found.'})

            current_year = date.today().year
            today = date.today()
            experience_years = (today - employee.created_on.date()).days // 365 if employee.created_on else 0

            policy = HolidayPolicy.objects.filter(
                year=current_year, min_years_experience__lte=experience_years
            ).order_by('-min_years_experience').first()
            floating_policy = FloatingHolidayPolicy.objects.filter(year=current_year).first()

            casual_leaves = (policy.ordinary_holidays_count if policy else 0) + (policy.extra_holidays if policy else 0)
            floating_leaves = floating_policy.allowed_floating_holidays if floating_policy else 0

            used_casual_leaves = leave_days_agg(
                LeaveRequest.objects.filter(
                    employee_user=request.user,
                    leave_type='Casual Leave',
                    status__in=['Accepted'],
                    start_date__year=current_year
                )
            )
            used_floating_leaves = leave_days_agg(
                LeaveRequest.objects.filter(
                    employee_user=request.user,
                    leave_type='Floating Leave',
                    status__in=['Accepted'],
                    start_date__year=current_year
                )
            )

            remaining_casual_leaves = (casual_leaves or 0) - (used_casual_leaves or 0)
            remaining_floating_leaves = (floating_leaves or 0) - (used_floating_leaves or 0)

            if remaining_casual_leaves <= 0 and remaining_floating_leaves <= 0:
                messages.error(request, "You have exhausted your Casual and Floating Leave entitlements for this year.")
                return redirect('request_leave')

            leave_type = request.POST.get('leave_type')
            original_leave_type = leave_type  # Keep track to distinguish conversion
            if leave_type == 'Casual Leave' and remaining_casual_leaves <= 0:
                messages.error(request, "No available Casual Leave left.")
                return redirect('request_leave')
            if leave_type == 'Floating Leave' and remaining_floating_leaves <= 0:
                messages.error(request, "No available Floating Leave left.")
                return redirect('request_leave')

            # Fetch holidays
            regular_holidays = set(Holiday.objects.filter(
                date__year=current_year
            ).values_list('date', flat=True))
            floating_holidays = set(FloatingHoliday.objects.filter(
                date__year=current_year
            ).values_list('date', flat=True))
            all_leave_dates = set(
                d for start, end in LeaveRequest.objects.filter(
                    employee_user=request.user,
                    status__in=['Pending', 'Accepted']
                ).values_list('start_date', 'end_date')
                for d in daterange(start, end)
            )

            start_date = leave_request.start_date
            end_date = leave_request.end_date
            requested_leave_dates = set(d for d in daterange(start_date, end_date))

            # Floating holidays in the range
            floating_holidays_in_range = [d for d in requested_leave_dates if d in floating_holidays]
            already_applied = [d for d in floating_holidays_in_range if d in all_leave_dates]
            not_applied = [d for d in floating_holidays_in_range if d not in all_leave_dates]
            floating_holiday_confirmed = request.POST.get('floating_holiday_confirmed') == 'true'

            # ====== Conversion Logic =======
            converted_to_casual = False
            if floating_holiday_confirmed or (
                leave_type == "Floating Leave" and used_floating_leaves + len(floating_holidays_in_range) > floating_leaves
            ):
                leave_type = "Casual Leave"
                converted_to_casual = True
                messages.info(request, f'Floating holidays in your range have been converted to casual leave or exceeded your entitlement.')

            if already_applied:
                messages.error(request, f"A leave is already applied for these floating holiday(s): {', '.join([d.strftime('%Y-%m-%d') for d in already_applied])}")
                return redirect('request_leave')

            # For Floating Leave type, must only select dates that are floating holidays!
            if original_leave_type == "Floating Leave" and not converted_to_casual:
                invalid_dates = [d for d in requested_leave_dates if d not in floating_holidays]
                if invalid_dates:
                    messages.error(request, 'The requested date range contains dates other than floating holidays.')
                    return redirect('request_leave')
                if used_floating_leaves + len(requested_leave_dates) > floating_leaves:
                    messages.error(request, 'Floating holiday limit exceeded. Request will be converted to casual leave on your next try.')
                    return redirect('request_leave')
                leave_duration = len(requested_leave_dates)
            else:
                if converted_to_casual:
                    leave_duration = sum(
                        1 for d in requested_leave_dates
                        if d.weekday() < 5 and d not in regular_holidays and d not in all_leave_dates
                    )
                else:
                    all_holidays = regular_holidays.union(floating_holidays)
                    leave_duration = sum(
                        1 for d in requested_leave_dates
                        if d.weekday() < 5 and d not in all_holidays and d not in all_leave_dates
                    )

            # --- Balance check again now that we know duration ---
            if leave_type == 'Casual Leave' and used_casual_leaves + leave_duration > casual_leaves:
                messages.error(request, f"Your requested leave exceeds your remaining Casual Leave balance ({remaining_casual_leaves} left).")
                return redirect('request_leave')

            if leave_type == "Floating Leave" and used_floating_leaves + leave_duration > floating_leaves:
                messages.error(request, 'Floating holiday limit exceeded. Request will be converted to casual leave.')
                return redirect('request_leave')

            # Save the request
            leave_request.leave_type = leave_type
            leave_request.status = 'Pending'
            leave_request.leave_days = leave_duration
            leave_request.save()

            # ==== EMAIL NOTIFICATION LOGIC ====
            manager = getattr(employee, 'manager', None)  # Adjust if your model relationship is different

            # Email to employee
            send_mail(
                subject="Leave Request Submitted",
                message=(
                    f"Dear {employee.first_name},\n\n"
                    f"Your leave request from {leave_request.start_date} to {leave_request.end_date} ({leave_request.leave_type}) "
                    "has been submitted and is pending your manager's approval.\n\n"
                    "Best regards,\nHR Team"
                ),
                from_email="akashaku32@gmail.com",
                recipient_list=[employee.company_email],
                fail_silently=False,
            )

            # Email to manager (if available)
            if manager and getattr(manager, 'company_email', None):
                send_mail(
                    subject="Leave Approval Required for Your Team Member",
                    message=(
                        f"Dear {manager.first_name},\n\n"
                        f"Employee {employee.first_name} {employee.last_name} has requested leave from {leave_request.start_date} to {leave_request.end_date} ({leave_request.leave_type}).\n\n"
                        "Please log in to the HR portal to review and approve or reject this leave request.\n\n"
                        "Best regards,\nHR Team"
                    ),
                    from_email="akashaku32@gmail.com",
                    recipient_list=[manager.company_email],
                    fail_silently=False,
                )

            messages.success(request, 'Leave request submitted successfully!')
            return redirect('request_leave')
    else:
        form = LeaveRequestForm(user=request.user)

    # --- Context for GET rendering remains unchanged (as before)
    try:
        employee = Employees.objects.get(company_email=request.user.email)
    except Employees.DoesNotExist:
        return render(request, 'employee_app/error.html', {'message': 'Employee details not found.'})

    is_manager = Employees.objects.filter(manager=employee).exists()
    current_year = date.today().year
    today = date.today()
    current_month = today.month
    experience_years = (today - employee.created_on.date()).days // 365 if hasattr(employee, 'created_on') and employee.created_on else 0

    policy = HolidayPolicy.objects.filter(
        year=current_year, min_years_experience__lte=experience_years
    ).order_by('-min_years_experience').first()
    floating_policy = FloatingHolidayPolicy.objects.filter(year=current_year).first()
    casual_leaves = (policy.ordinary_holidays_count if policy else 0) + (policy.extra_holidays if policy else 0)
    floating_leaves = floating_policy.allowed_floating_holidays if floating_policy else 0

    used_casual_leaves = leave_days_agg(
        LeaveRequest.objects.filter(
            employee_user=request.user, leave_type='Casual Leave', status__in=['Accepted'], start_date__year=current_year
        )
    )
    used_floating_leaves = leave_days_agg(
        LeaveRequest.objects.filter(
            employee_user=request.user, leave_type='Floating Leave', status__in=['Accepted'], start_date__year=current_year
        )
    )

    remaining_casual_leaves = (casual_leaves or 0) - (used_casual_leaves or 0)
    remaining_floating_leaves = (floating_leaves or 0) - (used_floating_leaves or 0)

    holidays = list(Holiday.objects.filter(date__year=current_year).values_list('date', flat=True))
    floating_holidays = list(FloatingHoliday.objects.filter(date__year=current_year).values_list('date', flat=True))
    approved_leave_dates = [
        d.strftime('%Y-%m-%d')
        for start, end in LeaveRequest.objects.filter(
            employee_user=request.user, status='Accepted'
        ).values_list('start_date', 'end_date')
        for d in daterange(start, end)
    ]
    pending_leave_dates = [
        d.strftime('%Y-%m-%d')
        for start, end in LeaveRequest.objects.filter(
            employee_user=request.user, status='Pending'
        ).values_list('start_date', 'end_date')
        for d in daterange(start, end)
    ]
    weekends = []
    day = date(current_year, current_month, 1)
    while day.month == current_month:
        if day.weekday() in [5, 6]:
            weekends.append(day)
        day += timedelta(days=1)

    context = {
        'form': form,
        'employee_name': f"{employee.first_name} {employee.last_name}",
        'employee_email': employee.company_email,
        'holidays': [d.strftime('%Y-%m-%d') for d in holidays],
        'floating_holidays': [d.strftime('%Y-%m-%d') for d in floating_holidays],
        'weekends': [d.strftime('%Y-%m-%d') for d in weekends],
        'approved_leave_dates': approved_leave_dates,
        'pending_leave_dates': pending_leave_dates,
        'is_manager': is_manager,
        'emp_designation': employee.designation,
        'emp_id': employee.employee_id,
        'emp_fname': employee.first_name,
        'emp_lname': employee.last_name,
        'casual_leaves': casual_leaves,
        'floating_leaves': floating_leaves,
        'used_casual_leaves': used_casual_leaves,
        'used_floating_leaves': used_floating_leaves,
        'remaining_casual_leaves': remaining_casual_leaves,
        'remaining_floating_leaves': remaining_floating_leaves,
    }
    return render(request, 'leaverequest.html', context)
@login_required
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
@login_required
def check_leave_conflicts(request):
    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # Only consider Pending or Accepted leaves
        leave_qs = LeaveRequest.objects.filter(
            employee_user=request.user,
            status__in=['Pending', 'Accepted']
        )

        # All leave dates for the user (pending/accepted only)
        leave_dates = set(
            d for start, end in leave_qs.values_list('start_date', 'end_date')
            for d in daterange(start, end)
        )

        # All floating holidays for the year
        current_year = date.today().year
        floating_holidays = set(FloatingHoliday.objects.filter(date__year=current_year).values_list('date', flat=True))

        # Dates in the selected range
        selected_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

        # Find conflicts (any leave already applied, except rejected)
        conflict_dates = [d.strftime('%Y-%m-%d') for d in selected_dates if d in leave_dates]

        # Find floating holidays in range that are not already applied for
        floating_holiday_not_applied = [
            d.strftime('%Y-%m-%d') for d in selected_dates
            if d in floating_holidays and d not in leave_dates
        ]

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
        # Only revert counters if leave was "Accepted" or "Approved"
        if leave.status in ["Accepted", "Approved"]:
            # You may want to recompute the duration as you did on accept_leave_request!
            # For a simple rollback, assume leave.leave_days is correct:
            # If you tracked floating vs casual breakdown, you'd subtract accordingly
            
            # Here is a generic rollback (customize by your app logic):
            employee.used_leaves = max(0, employee.used_leaves - (leave.leave_days or 0))
            # If you also need to handle floating leave, and you track that breakdown, adjust as needed.
            # Example: employee.floating_holidays_used = max(0, employee.floating_holidays_used - float_days_of_this_leave)
            employee.save()
        leave.delete()
        messages.success(request, "Planned leave deleted successfully.")
    else:
        messages.error(request, "Invalid delete operation.")
    return redirect('my_leave_history') # Make sure this name matches your leave history view name

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import LeaveRequest,HolidayPolicy,FloatingHolidayPolicy
from django.db.models import Sum, Q
from django.utils.timezone import now

@login_required

def my_leave_history(request):
    user = request.user
    current_year = now().year
    today = now().date()
    
    start_of_year = date(current_year, 1, 1)
    end_of_year = date(current_year, 12, 31)

# Format as "Jan 1, 2024 - Dec 31, 2024"
    validity_range = f"{start_of_year.strftime('%b %d, %Y')} - {end_of_year.strftime('%b %d, %Y')}"

    # --- Filtering ---
    status_filter = request.GET.get('status', '')  # This comes from the dropdown

    leave_requests = LeaveRequest.objects.filter(employee_user=user).order_by('-start_date')

    # Apply filtering if filter chosen
    if status_filter == 'pending':
        leave_requests = leave_requests.filter(status__iexact='Pending')
    elif status_filter == 'upcoming':
        leave_requests = leave_requests.filter(
            status__in=['Accepted', 'Approved'],
            end_date__gte=today
        )
    elif status_filter == 'accepted':
        leave_requests = leave_requests.filter(status__in=['Accepted', 'Approved'])
    elif status_filter == 'rejected':
        leave_requests = leave_requests.filter(status__iexact='Rejected')

    # Add convenience flags for template
    for leave in leave_requests:
        leave.is_pending = (leave.status == 'Pending')
        leave.is_approved = (leave.status in ['Accepted', 'Approved'])
        leave.is_rejected = (leave.status == 'Rejected')

    # ...all the rest of your code unchanged...
    try:
        employee = Employees.objects.get(user=user)
        is_manager = employee.employees_managed.exists()
        if getattr(employee, 'created_on', None):
            experience_years = (now().date() - employee.created_on.date()).days // 365
        else:
            experience_years = 0
    except Employees.DoesNotExist:
        employee = None
        is_manager = False
        experience_years = 0

    policy = (
        HolidayPolicy.objects
            .filter(year=current_year, min_years_experience__lte=experience_years)
            .order_by('-min_years_experience')
            .first()
    )
    floating_policy = FloatingHolidayPolicy.objects.filter(year=current_year).first()

    leave_summary_data = []
    for leave_type, description in LeaveRequest.LEAVE_TYPES:
        leave_type_key = leave_type.lower()

        if leave_type_key == "ordinary":
            total_leaves = policy.ordinary_holidays_count if policy else 0
        elif leave_type_key == "casual leave":
            total_leaves = (
                (policy.ordinary_holidays_count if policy else 0)
                + (policy.extra_holidays if policy else 0)
            )
        elif leave_type_key == "floating leave":
            total_leaves = floating_policy.allowed_floating_holidays if floating_policy else 0
        else:
            total_leaves = 0

        used_leaves = (
            LeaveRequest.objects
                .filter(
                    employee_user=user,
                    leave_type=leave_type,
                    start_date__year=current_year,
                    status__in=["Accepted", "Approved"],
                    end_date__lt=today,  # Add this line!
                )
                .aggregate(total_days=Sum('leave_days'))['total_days'] or 0
)
        planned_leaves = (
            LeaveRequest.objects
                .filter(
                    employee_user=user,
                    leave_type=leave_type,
                    start_date__year=current_year,
                    status__in=["Accepted", "Approved"],
                    end_date__gte=today,
                )
                .aggregate(total_days=Sum('leave_days'))['total_days'] or 0
        )

        leave_summary_data.append({
            'leave_type': description,
            'validity': validity_range,
            'available': max(0, total_leaves - used_leaves - planned_leaves),
            'used': used_leaves,
            'planned': planned_leaves,
        })

    total_used_leaves = sum(item['used'] for item in leave_summary_data)

    planned_leave_requests = (
        LeaveRequest.objects
            .filter(
                employee_user=user,
                status__in=["Accepted", "Approved"],
                start_date__year=current_year,
                end_date__gte=today,
            )
            .order_by('start_date')
    )

    # Pass request as context for context-aware selection of the dropdown in template
    return render(request, 'my_leave_history.html', {
        'leave_requests': leave_requests,
        'leave_summary': leave_summary_data,
        'is_manager': is_manager,
        'emp_designation': employee.designation if employee else '',
        'emp_id': employee.employee_id if employee else '',
        'emp_fname': employee.first_name if employee else '',
        'emp_lname': employee.last_name if employee else '',
        'total_used_leaves': total_used_leaves,
        'planned_leave_requests': planned_leave_requests,
        'request': request,
        "today": date.today()  # <--- Add this!
    })
from django.utils.timezone import now

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
        'emp_designation': employee.designation,  # Employee designation
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
            employee = Employees.objects.get(company_email=request.user.email)
            is_manager = employee.employees_managed.exists()  # Checks if they manage anyone
        except Employees.DoesNotExist:
            pass  # If no employee record is found, keep is_manager as False

    current_year = now().year  # Get current year
    total_used_leaves = employee.used_leaves  # Fetch from the Employees model

    context = {
        'holidays': holidays,
        'floating_holidays': floating_holidays,
        'is_manager': is_manager,  # Pass manager status to template
        'emp_designation': employee.designation,  # Employee designation
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


@login_required
def manager_leave_requests(request):
    """View to list leave requests submitted by subordinates."""
    try:
        # Fetch the logged-in user's employee profile
        manager = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        return render(request, 'employee_app/error.html', {'message': 'Manager profile not found.'})

    # Ensure the logged-in user is a manager
    if not Employees.objects.filter(manager=manager).exists():
        return HttpResponse("cannot access")

    # Check if the employee is a manager
    is_manager = Employees.objects.filter(manager=manager).exists()

    current_year = now().year
    total_used_leaves = manager.used_leaves

    # Filter leave requests for employees managed by the logged-in manager
    leave_requests = LeaveRequest.objects.filter(employee_master__manager=manager)

    # Get available years for filtering
    available_years = list(set(leave_requests.values_list('start_date__year', flat=True)))

    return render(request, 'manage_leave_requests.html', {
        'leave_requests': leave_requests,
        'manager_name': f"{manager.first_name} {manager.last_name}",
        'is_manager': is_manager,
        'emp_designation': manager.designation,
        'emp_id': manager.employee_id,
        'emp_fname': manager.first_name,
        'emp_lname': manager.last_name,
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

@login_required
def manage_leave_request(request, leave_request_id):
    leave_request = get_object_or_404(LeaveRequest, id=leave_request_id)

    # Ensure the logged-in manager or admin is allowed to act on this leave request
    if not request.user.is_superuser and leave_request.employee_master.manager.user != request.user:
        return render(request, 'employee_app/error.html', {'message': 'Unauthorized action.'})

        # Get the logged-in employee
    try:
        logged_in_employee = Employees.objects.get(user=request.user)
    except Employees.DoesNotExist:
        return render(request, 'employee_app/error.html', {'message': 'Employee profile not found.'})

        # Check if the logged-in employee is a manager
    is_manager = Employees.objects.filter(manager=logged_in_employee).exists()

    current_year = now().year  # Get current year
    total_used_leaves = logged_in_employee.used_leaves  # Fetch from the Employees model

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
            print(f"Current Used Leaves: {employee.used_leaves}")
            print(f"Current Total Leaves: {employee.total_leaves}")

            # Check if the employee has enough leave balance
            if employee.used_leaves + leave_duration <= 15:
                # Update leave days and floating holidays used
                employee.used_leaves += leave_duration
                employee.floating_holidays_used = floating_holidays_used
                employee.save()
                print(f"Updated Used Leaves: {employee.used_leaves}")
            else:
                messages.error(request, "Employee cannot exceed the allowed 15 total leave days.")
                return redirect('manager_leave_requests')  # Or redirect to another appropriate view

        elif action == 'reject':
            leave_request.status = 'Rejected'

        # Set `approved_by` to the user who approved or rejected the leave
        if request.user.is_superuser:
            leave_request.approved_by = request.user  # Admin approves
        else:
            approver = leave_request.employee_master.manager.user
            leave_request.approved_by = approver  # Manager approves

        leave_request.save()

        return redirect('manager_leave_requests' if not request.user.is_superuser else 'admin_leave_requests')

    return render(request, 'manage_leave_requests.html', {'leave_request': leave_request,'is_manager' : is_manager ,'emp_designation':logged_in_employee.designation , 'emp_id' : logged_in_employee.employee_id , 'emp_fname' : logged_in_employee.first_name , 'emp_lname' : logged_in_employee.last_name , 'total_used_leaves' : total_used_leaves})










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
    subordinates = Employees.objects.filter(manager=manager)

    # Check if the logged-in employee is actually a manager
    is_manager = subordinates.exists()  # If they have subordinates, they're a manager

    current_year = now().year  # Get current year
    total_used_leaves = manager.used_leaves  # Fetch from the Employees model

    return render(request, 'view_subordinates.html', {
        'subordinates': subordinates,
        'manager': manager,
        'is_manager' : is_manager,
        'emp_id' : manager.employee_id ,
        'emp_fname' : manager.first_name,
        'emp_lname' : manager.last_name,
        'emp_designation' : manager.designation,
        'total_used_leaves' : total_used_leaves
    })



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from datetime import datetime
from .models import Employees, LeaveRequest, Holiday, FloatingHoliday
from admin_app.utils import calculate_leave_days  # Ensure correct function is imported

from django.core.mail import send_mail
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime

def allocate_leave(request, manager_id):
    """Manager can allocate leave for a subordinate."""
    manager = get_object_or_404(Employees, user=request.user)
    employee = get_object_or_404(Employees, id=manager_id)
    current_year = datetime.now().year  # Get current year
    total_used_leaves = employee.used_leaves  # Fetch from Employees model

    # Determine if the logged-in user is a manager
    is_manager = Employees.objects.filter(manager=manager).exists()

    if request.method == "POST":
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")
        reason = request.POST.get("reason", "").strip()

        if not start_date_str or not end_date_str:
            messages.error(request, "Both start and end date are required.")
            return render(request, 'allocate_leave.html', {'employee': employee})

        if not reason:
            messages.error(request, "Reason is required.")
            return render(request, 'allocate_leave.html', {'employee': employee})

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return render(request, 'allocate_leave.html', {'employee': employee})

        if end_date < start_date:
            messages.error(request, "End date cannot be before start date.")
            return render(request, 'allocate_leave.html', {'employee': employee})

        # Simple plain calculation: total days including both ends
        leave_days = (end_date - start_date).days + 1
        print(leave_days)
        if leave_days <= 0:
            messages.error(request, "No valid leave days selected.")
            return render(request, 'allocate_leave.html', {'employee': employee})

        # Ensure the employee has enough leave balance
        if employee.used_leaves + leave_days > employee.total_leaves:
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
            status="Approved",
            leave_days=leave_days
        )

        # Update employee leave balance
        employee.used_leaves += leave_days
        employee.save()

        # Send email notification
        send_mail(
            subject="Leave Allocation Notification",
            message=(
                f"Dear {employee.first_name},\n\n"
                f"Your manager {manager.first_name} {manager.last_name} has allocated leave for you from {start_date} to {end_date}.\n\n"
                f"Number of days: {leave_days}\n"
                f"Reason: {reason}\n\n"
                "Best regards,\nHR Team"
            ),
            from_email="akashaku32@gmail.com",
            recipient_list=[employee.company_email],
            fail_silently=False,
        )

        messages.success(request, f"Leave has been allocated to {employee.first_name} {employee.last_name}.")
        return redirect('view_subordinates')

    return render(request, 'allocate_leave.html', {
        'employee': employee,
        'emp_id': manager.employee_id,
        'emp_fname': manager.first_name,
        'emp_lname': manager.last_name,
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