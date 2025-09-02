from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.conf import settings
from functools import wraps
import datetime
import time
from django.contrib.auth.decorators import login_required
from .utils import get_leave_policy_details
from .models import LeaveDetails
TIMEOUT_DURATION = 60 * 60  # 60 minutes

def signin_required(fn):
    @wraps(fn)
    def wrapper(request, *args, **kwargs):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return redirect("login")
        
        # Check if the session has timed out due to inactivity
        current_time = int(time.time())
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
import time

def employee_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')  # emp_email
        password = request.POST.get('password')

        recaptcha_response = request.POST.get('g-recaptcha-response')  # Get captcha token from frontend

        #  Verify reCAPTCHA with Google
        data = {
            'secret': settings.RECAPTCHA_PRIVATE_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()

        if not result.get('success'):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return redirect('login')
        
        user_obj = User.objects.filter(email__iexact=email).first()
        if not user_obj:
            messages.error(request, 'Invalid password.')
            return redirect('login')


        # Authenticate with email as the username
        user= authenticate(request, username=user_obj.email, password=password)
        print(user)
        if user is not None:
            login(request, user)  # Log the user in

            # to initialize session activity tracking
            request.session['last_activity'] = int(time.time())

            if user.check_password("defaultpassword"):
                return redirect('set_password')  # Redirect to the set password page

            return redirect('emp_dashboard')  # Redirect to employee dashboard
        else:
            messages.error(request, 'Invalid credentials')
            # return HttpResponse("invalid credentials")
            return redirect('login')  # Redirect back to login page

    return render(request, 'emp_login.html',{'recaptcha_site_key': settings.RECAPTCHA_PUBLIC_KEY})



#dashboard view of employee
@signin_required
def dashboard_view(request):
    try:
        employee = Employees.objects.get(company_email=request.user.username)
    except Employees.DoesNotExist:
        messages.error(request, 'Employee record not found. Please contact admin.')
        return redirect('login')

    return render(request, 'emp_dashboard.html', {
        'employee': employee,
        'emp_id': employee.employee_id,
        'emp_fname': employee.first_name,
        'emp_lname': employee.last_name,
        'emp_designation': employee.role.role_name,
    })


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
            return redirect('emp_dashboard')
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


from django.shortcuts import render, get_object_or_404
from .models import Employees
from django.utils.timezone import now
from datetime import date, timedelta
def set_from_timesheet(request, employee_id):
    """
    Marks in the session that the user came to the employee page from the timesheet.

    This helps us remember where the user came from so we can show the right left-sidebar element according to that.
    """

    request.session['from_timesheet'] = True
    return redirect('profile', employee_id=employee_id)
@signin_required
def employee_profile(request, employee_id):
    from_timesheet = request.session.pop('from_timesheet', False)
 
    base_template = 'partials/base.html'
    if from_timesheet:
        base_template = 'timesheet_partials/base.html'
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
    experience_years = (today - employee.enc_valid_from).days // 365 if employee.enc_valid_from else 0

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
    quota = (policy.ordinary_holidays_count if policy else 0) \
            + (policy.extra_holidays if policy else 0) \
            + (floating_policy.allowed_floating_holidays if floating_policy else 0)

    available_leaves = max(0, quota - used_leaves - planned_leaves)
   
    is_manager = Employees.objects.filter(manager=employee, is_deleted=False).exists()

    return render(request, 'profile.html', {
        'base_template':base_template ,
        'employee': employee,
        'is_manager': is_manager,
        'available_leaves': available_leaves,  # <--- ONLY this number!
    })


from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Employees
# employee_app/views.py
from django.shortcuts import redirect
from django.contrib.auth import logout

def employee_logout(request):
    logout(request)  # Logs out the employee
    return redirect('login')  # Redirect to login page after logout



from django.http import JsonResponse
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
from dateutil.relativedelta import relativedelta
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
        experience_years = (today - employee.enc_valid_from).days // 365 if employee.enc_valid_from else 0
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

        # fy_end extended because it is needed for next year leave request from current year
        fy_end_extended = fy_end + relativedelta(months=9) 


        # Dates from country-based holidays
        country_holiday_dates = set(
            Holiday.objects.filter(
                country=employee.country,
                date__range=(fy_start, fy_end_extended)
            ).values_list('date', flat=True)
        )

        # Dates from state-based holidays
        state_holiday_dates = set(
            StateHoliday.objects.filter(
                state=employee.state,
                date__range=(fy_start, fy_end_extended)
            ).values_list('date', flat=True)
        )

        # Combine both sets
        holidays = country_holiday_dates | state_holiday_dates
        floating_holidays = set(
            FloatingHoliday.objects.filter(
                country=employee.country,
                date__range=(fy_start, fy_end_extended)
            ).values_list('date', flat=True)
        )

        state_excluded = set(
        StateHoliday.objects.filter(
            country=employee.country,
            date__range=(fy_start, fy_end_extended)
        ).exclude(
            state=employee.state
        ).values_list('date', flat=True)
        )

        # Final floating = union of floating + excluded, minus holidays
        floating = (floating_holidays | state_excluded) - holidays
        

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

            #financial year
            current_year=date.today().year


            if fy_start <= leave_request.start_date <= fy_end:
                pass
            elif leave_request.start_date > fy_end:
                current_year += 1 
            else:
                current_year-=1

            leave_details=get_leave_policy_details(employee,current_year)
            holiday_policy = leave_details['allowed_holiday_policy']
            if not holiday_policy:
                messages.error(request,f"No holiday policy configured for the year {current_year} . contact the manager")
                return redirect('request_leave')
            emp_leave_details, created = LeaveDetails.objects.get_or_create(employee=employee,year=current_year,defaults={"total_casual_leaves":holiday_policy})



            leave_request.employee_user = request.user
            leave_request.employee_master = employee

            day_type = request.POST.get('day_type')
            if day_type == 'one':
                leave_request.end_date = leave_request.start_date
                leave_request.leave_days=1
            else:
                if not leave_request.end_date or leave_request.end_date < leave_request.start_date:
                    messages.error(request, "Please select a valid End Date.")
                    return redirect('request_leave')
            
            holidays, floating_holidays = get_holidays(employee, fy_start, fy_end)
            # Pre-batch all leaves once
            all_leaves = get_leave_requests(request.user, fy_start, fy_end + relativedelta(months=9))
            used_casual_leaves = emp_leave_details.casual_leaves_used if emp_leave_details else 0
            used_floating_leaves = emp_leave_details.floating_holidays_used if emp_leave_details else 0
            pending_casual_leaves = emp_leave_details.pending_casual if emp_leave_details else 0
            pending_floating_leaves = emp_leave_details.pending_float if emp_leave_details else 0
            planned_casual=emp_leave_details.planned_casual if emp_leave_details else 0
            planned_float=emp_leave_details.planned_float if emp_leave_details else 0

            if emp_leave_details:
                casual_leaves=emp_leave_details.total_casual_leaves
            else:
                casual_leaves = (policy.ordinary_holidays_count if policy else 0) + (policy.extra_holidays if policy else 0)
            floating_leaves = floating_policy.allowed_floating_holidays if floating_policy else 0
            remaining_casual_leaves = (casual_leaves or 0) - (used_casual_leaves or 0) - (pending_casual_leaves or 0) - (planned_casual or 0)
            remaining_floating_leaves = (floating_leaves or 0) - (used_floating_leaves or 0) - (pending_floating_leaves or 0) - (planned_float or 0)
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

            #updating employee leave record
            if leave_type == "Casual Leave":
                emp_leave_details.pending_casual = (emp_leave_details.pending_casual or 0) + leave_duration
            elif leave_type == "Floating Leave":
                emp_leave_details.pending_float = (emp_leave_details.pending_float or 0) + leave_duration
            emp_leave_details.save()

            # Email to Employee
            send_mail(
                subject="Leave Request Submitted",
                message=(
                    f"Dear {employee.first_name},\n\n"
                    f"Your leave request has been submitted successfully.\n\n"
                    f"Leave Type: {leave_request.leave_type}\n"
                    f"Leave Period: {leave_request.start_date.strftime('%B %d, %Y')} to {leave_request.end_date.strftime('%B %d, %Y')}\n"
                    f"Total Days: {leave_request.leave_days} days\n"
                    
                    f"Reason: {leave_request.reason}\n"
                    f"Status: Pending Approval\n\n"
                    f"Best regards,\nHR Team"
                ),
                from_email="lms@spectrasoln.com",
                recipient_list=[employee.company_email],
                fail_silently=False,
            )

          
        # Email to Manager
            if manager and getattr(manager, 'company_email', None):
                send_mail(
                    subject=f"Leave Approval Required - {employee.first_name} {employee.last_name}",
                    message=(
                        f"Dear {manager.first_name},\n\n"
                        f"Employee {employee.first_name} {employee.last_name} has submitted a leave request.\n\n"
                        
                        f"Employee ID: {employee.employee_id}\n"
                        f"Leave Type: {leave_request.leave_type}\n"
                        f"Leave Period: {leave_request.start_date.strftime('%B %d, %Y')} to {leave_request.end_date.strftime('%B %d, %Y')}\n"
                        f"Total Days: {leave_request.leave_days} days\n"
                        
                        f"Reason: {leave_request.reason}\n"
                        f"Employee's Leave Balance: {emp_leave_details.total_casual_leaves - emp_leave_details.casual_leaves_used} days remaining\n\n"
                        f"Please review the request in the HR system.\n"
                        f"Login here: {approval_url}\n\n"
                        f"Best regards,\nHR Team"
                    ),
                    from_email="lms@spectrasoln.com",
                    recipient_list=[manager.company_email],
                    fail_silently=False,
                )

                # Email to PM (if PM email exists)
            if employee.pm_email:
                send_mail(
                    subject=f"Leave Request Notification - {employee.first_name} {employee.last_name}",
                    message=(
                        f"Dear Project Manager,\n\n"
                        f"{employee.first_name} {employee.last_name} has applied for leave.\n\n"
                        f"Employee ID: {employee.employee_id}\n"
                        f"Leave Type: {leave_request.leave_type}\n"
                        f"Leave Period: {leave_request.start_date} to {leave_request.end_date}\n"
                        f"Total Days: {leave_request.leave_days} days\n"
                        
                        f"Reason: {leave_request.reason}\n"
                        f"Status: Pending Approval\n\n"
                        f"This is for your information. The leave request is pending approval from the reporting manager.\n\n"
                        f"Best regards,\nHR Team"
                    ),
                    from_email="lms@spectrasoln.com",
                    recipient_list=[employee.pm_email],
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
        experience_years = (today - employee.enc_valid_from).days // 365 if employee.enc_valid_from else 0
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

        reset_period = HolidayResetPeriod.objects.filter(country=employee.country).first()
    
        year_to_use= date.today().year-1 if date.today().month < reset_period.start_month else date.today().year
        employee_leaves=LeaveDetails.objects.filter(employee=employee,year=year_to_use).first()
        if employee_leaves:
            casual_leaves=employee_leaves.total_casual_leaves
        else:
            casual_leaves = (policy.ordinary_holidays_count if policy else 0) + (policy.extra_holidays if policy else 0)
        floating_leaves = floating_policy.allowed_floating_holidays if floating_policy else 0
        holidays, floating_holidays = get_holidays(employee, fy_start, fy_end)

        # Only call DB for all leaves ONCE!
        all_leaves = get_leave_requests(request.user, fy_start, fy_end + relativedelta(months=9))

        used_casual_leaves = employee_leaves.casual_leaves_used if employee_leaves else 0
        used_floating_leaves = employee_leaves.floating_holidays_used if employee_leaves else 0
        used_pending_casual_leaves = employee_leaves.pending_casual if employee_leaves else 0
        used_pending_floating_leaves = employee_leaves.pending_float if employee_leaves else 0
        planned_casual=employee_leaves.planned_casual if employee_leaves else 0
        planned_float=employee_leaves.planned_float if employee_leaves else 0

        remaining_casual_leaves = (casual_leaves or 0) - (used_casual_leaves or 0) - (used_pending_casual_leaves or 0) - (planned_casual or 0)
        remaining_floating_leaves = (floating_leaves or 0) - (used_floating_leaves or 0) - (used_pending_floating_leaves or 0) - (planned_float or 0)
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
            'fy_end_calender': fy_end
        }
        return render(request, 'leaverequest.html', context)

from django.core.mail import send_mail
from django.http import HttpResponse



# this view is used for displaying next year count in employee request leave
@login_required
def get_next_year_leave_counts(request):

    # take the financial year  
    fy_end = request.GET.get("fy_end_year")
    employee_id = request.GET.get("employee_id")
    
    # convert the fy_end to date object
    fy_end_date = datetime.strptime(fy_end, "%Y-%m-%d").date()

    # add one month to take the next FY year since fy_end_date is the last month of current FY
    next_year = (fy_end_date + relativedelta(months = 1)).year

    # fetch the employee
    if employee_id:
        employee = Employees.objects.get(id = employee_id)
    else:
        employee= Employees.objects.get(user=request.user)

    # fetching employee leave count of next year 
    leave_details=get_leave_policy_details(employee,next_year)
    holiday_policy = leave_details['allowed_holiday_policy']
    floating_holiday_policy = leave_details['allowed_floating_holiday_policy']

    if not (holiday_policy and floating_holiday_policy):
        messages.error(request,f"No holiday policy configured for the year {next_year} . contact the manager")
        return redirect('request_leave')
    employee_leaves, created = LeaveDetails.objects.get_or_create(employee=employee,year=next_year,defaults={"total_casual_leaves":holiday_policy})

    casual_leaves = employee_leaves.total_casual_leaves if employee_leaves else 0
    used_casual_leaves = employee_leaves.casual_leaves_used if employee_leaves else 0
    used_floating_leaves = employee_leaves.floating_holidays_used if employee_leaves else 0
    used_pending_casual_leaves = employee_leaves.pending_casual if employee_leaves else 0
    used_pending_floating_leaves = employee_leaves.pending_float if employee_leaves else 0
    planned_casual=employee_leaves.planned_casual if employee_leaves else 0
    planned_float=employee_leaves.planned_float if employee_leaves else 0

    next_year_casual = (casual_leaves or 0) - (used_casual_leaves or 0) - (used_pending_casual_leaves or 0) - (planned_casual or 0)
    next_year_floating = (floating_holiday_policy or 0) - (used_floating_leaves or 0) - (used_pending_floating_leaves or 0) - (planned_float or 0)

    return JsonResponse({
        "remaining_casual_leaves": next_year_casual,
        "remaining_floating_leaves": next_year_floating,
    })


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
            start_date__lte=fy_end_date + relativedelta(months=9),
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
            date__lte=fy_end_date + relativedelta(months=9)
        ).values_list('date', flat=True))
        state_excluded = set(
        StateHoliday.objects.filter(
            country=country,
            date__gte=fy_start_date,
            date__lte=fy_end_date + relativedelta(months=9)
        ).exclude(
            state=employee_profile.state
        ).values_list('date', flat=True)
        )

        floating_holidays |=state_excluded

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
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import LeaveRequest

def delete_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, pk=leave_id, employee_user=request.user)
    employee = leave.employee_master
    current_year=date.today().year
    reset_period = HolidayResetPeriod.objects.filter(country=employee.country).first()
    if reset_period:
        start_month = reset_period.start_month
        start_day = reset_period.start_day
        end_month=reset_period.end_month
        end_day=reset_period.end_day
        financial_year_start_date = date(current_year, start_month, start_day)
        financial_year_end_date = date(current_year+1, end_month, end_day)

    if financial_year_start_date <= leave.start_date <= financial_year_end_date:
        pass
    elif leave.start_date > financial_year_end_date:
        current_year +=1
    else:
        current_year-=1

    emp_leave_details = LeaveDetails.objects.get(employee=employee,year=current_year)
    if request.method == "POST":
        if leave.status in ["Accepted", "Approved"]:
            if leave.leave_type == "Floating Leave":
                emp_leave_details.planned_float = max(0, emp_leave_details.planned_float - (leave.leave_days or 0))
            else:  # For "Casual Leave", "Sick Leave", etc.
                emp_leave_details.planned_casual = max(0, emp_leave_details.planned_casual - (leave.leave_days or 0))
            emp_leave_details.save()
        
        elif leave.status == "Pending":
            if leave.leave_type == "Floating Leave":
                emp_leave_details.pending_float = max(0, emp_leave_details.pending_float - (leave.leave_days or 0))
            else:  # For "Casual Leave", 
                emp_leave_details.pending_casual = max(0, emp_leave_details.pending_casual - (leave.leave_days or 0))
            emp_leave_details.save()     
            
        
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
from .models import LeaveRequest,HolidayPolicy,FloatingHolidayPolicy,Employees, LeaveRequest, HolidayPolicy, FloatingHolidayPolicy, HolidayResetPeriod
from django.db.models import Sum, Q
from django.utils.timezone import now
from datetime import date, datetime, timedelta

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
    experience_years = (today - employee.enc_valid_from).days // 365 if employee and employee.enc_valid_from else 0

    # Batch get policies and all holidays, reusing them
    policy = None
    floating_policy = None
    holidays = []
    floating_holidays = []

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

        holidays = set(
            Holiday.objects.filter(
                country=employee.country,
                date__range=(fin_year_start, fin_year_end)
            ).values_list('date', flat=True)
        )
        state_holiday_dates = set(
            StateHoliday.objects.filter(
                state=employee.state,
                date__range=(fin_year_start, fin_year_end)
            ).values_list('date', flat=True)
        )
        #combine both 
        holidays |= state_holiday_dates

        
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
        leave_type_lower = leave_type.lower()
        total_leaves = 0
        used_leaves = 0
        planned_leaves = 0
        pending_leaves = 0

        year_to_use = date.today().year - 1 if date.today().month < reset_period.start_month else date.today().year
        leave_details=get_leave_policy_details(employee,year_to_use)
        holiday_policy = leave_details['allowed_holiday_policy']
        employee_leaves, created = LeaveDetails.objects.get_or_create(employee=employee, year=year_to_use,defaults={"total_casual_leaves":holiday_policy})
        lvs = leaves_by_type.get(leave_type, [])

        if leave_type_lower == "casual leave":


            updated_used = sum(
                overlapping_leave_days(l.start_date, l.end_date, fin_year_start, fin_year_end, holidays_set)
                for l in lvs if l.status in ['Accepted', 'Approved'] and l.end_date < today
            )

            if employee_leaves and updated_used != employee_leaves.casual_leaves_used:
                diff=updated_used-employee_leaves.casual_leaves_used
                employee_leaves.casual_leaves_used = updated_used
                employee_leaves.planned_casual = max(0, (employee_leaves.planned_casual or 0) - diff)
                employee_leaves.save()

            used_leaves = employee_leaves.casual_leaves_used

            if employee_leaves:
                total_leaves = employee_leaves.total_casual_leaves or 0
                planned_leaves = employee_leaves.planned_casual or 0
                pending_leaves = employee_leaves.pending_casual or 0 

        elif leave_type_lower == "floating leave":
            total_leaves = floating_policy.allowed_floating_holidays if floating_policy else 0


            updated_used = sum(
                overlapping_leave_days(l.start_date, l.end_date, fin_year_start, fin_year_end, holidays_set)
                for l in lvs if l.status in ['Accepted', 'Approved'] and l.end_date < today
            )

            if employee_leaves and updated_used != employee_leaves.floating_holidays_used:
                diff=updated_used-employee_leaves.floating_holidays_used
                employee_leaves.floating_holidays_used = updated_used
                employee_leaves.planned_float = max(0, (employee_leaves.planned_float or 0) - diff)
                employee_leaves.save()

            used_leaves = employee_leaves.floating_holidays_used

            if employee_leaves:
                planned_leaves = employee_leaves.planned_float or 0
                pending_leaves = employee_leaves.pending_float or 0

        elif leave_type_lower == "ordinary":
            total_leaves = policy.ordinary_holidays_count if policy else 0

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
    sidebar_template = 'partials/left-sidebar.html'

    if '/timesheet/' in request.path:
        sidebar_template = 'timesheet_partials//left-sidebar.html'

   
    try:
        employee = Employees.objects.get(company_email=request.user.username)
    except Employees.DoesNotExist:
        return render(request, 'error.html', {'message': 'Employee not found.'})

    # Check if the employee is a manager (has subordinates)
    if employee.employees_managed.exists():  # If there are employees managed by this employee
        is_manager = True
    else:
        is_manager = False





    return render(request, 'emp_index.html', {
        'employee': employee,
        'is_manager': is_manager , # Pass whether the employee is a manager or not
        'emp_designation': employee.role.role_name,  # Employee designation
        'emp_id': employee.employee_id,  # Employee ID
        'emp_fname' : employee.first_name, #employee firstname
        'emp_lname' : employee.last_name ,#employee lastname
        'sidebar_template':sidebar_template
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
# to get all the holidays in a year
from django.shortcuts import render
from datetime import date
from .models import Holiday, FloatingHoliday
from admin_app.models import StateHoliday
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

    #get financial year
    reset_period=HolidayResetPeriod.objects.filter(country=employee.country).first()
    if reset_period:
        start_month = reset_period.start_month
        start_day = reset_period.start_day
        end_month=reset_period.end_month
        end_day=reset_period.end_day
        if date.today().month < start_month:
            current_year=date.today().year-1
        else:
            current_year=date.today().year
        financial_year_start_date = date(current_year, start_month, start_day)
        financial_year_end_date = date(current_year+2, end_month, end_day)
    
    country_holidays = Holiday.objects.filter(country=employee.country).order_by('date')
    state_holidays=StateHoliday.objects.filter(country=employee.country,state=employee.state).order_by('date')
    holidays=[]
    holidays.extend([{
            'name': holiday.name,
            'date': holiday.date
        } for holiday in country_holidays if financial_year_start_date <= holiday.date <= financial_year_end_date])
    holidays.extend([{
            'name': holiday.name,
            'date': holiday.date
        } for holiday in state_holidays if financial_year_start_date <= holiday.date <= financial_year_end_date])

    holidays.sort(key=lambda x:x['date'])


    floating_holidays1 = FloatingHoliday.objects.filter(country=employee.country).order_by('date')
    floating_holidays2 = StateHoliday.objects.filter(country=employee.country).exclude(state=employee.state).order_by('date')

    # Build a set of (name, date) in holidays for quick comparison
    holiday_name_date_set = set((h['name'], h['date']) for h in holidays)

    floating_holidays = []
    floating_name_date_set = set()  # To prevent duplicates in floating holidays

    # Process floating_holidays1
    for holiday in floating_holidays1:
        entry = (holiday.name, holiday.date)
        if (financial_year_start_date <= holiday.date <= financial_year_end_date and
            entry not in holiday_name_date_set):
            floating_holidays.append({'name': holiday.name, 'date': holiday.date})
            floating_name_date_set.add(entry)

    # Process floating_holidays2 (from other states), avoid duplicates
    for holiday in floating_holidays2:
        entry = (holiday.name, holiday.date)
        if (financial_year_start_date <= holiday.date <= financial_year_end_date and
            entry not in holiday_name_date_set and
            entry not in floating_name_date_set):
            floating_holidays.append({'name': holiday.name, 'date': holiday.date})
            floating_name_date_set.add(entry)


    floating_holidays.sort(key=lambda x:x['date'])

    # Check if the logged-in user is a manager
    
    current_year = now().year  # Get current year


    context = {
        'employee':employee,
        'holidays': holidays,
        'floating_holidays': floating_holidays,
        'is_manager': is_manager,  # Pass manager status to template
        'emp_designation': employee.role.role_name,  # Employee designation
        'emp_id': employee.employee_id,  # Employee ID
        'emp_fname': employee.first_name,  # employee firstname
        'emp_lname': employee.last_name , # employee lastname
        # 'total_used_leaves' : total_used_leaves
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
        start_date__lte=fy_end + relativedelta(months=9),
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
    
    if request.method == 'POST':
        action = request.POST.get('action')
        start_date = leave_request.start_date
        end_date = leave_request.end_date
        employee = leave_request.employee_master

        # picking the correct Financial year
        current_year=date.today().year
        reset_period = HolidayResetPeriod.objects.filter(country=employee.country).first()
        if reset_period:
            start_month = reset_period.start_month
            start_day = reset_period.start_day
            end_month=reset_period.end_month
            end_day=reset_period.end_day
            financial_year_start_date = date(current_year, start_month, start_day)
            financial_year_end_date = date(current_year+1, end_month, end_day)

        if financial_year_start_date <= leave_request.start_date <= financial_year_end_date:
            pass
        elif leave_request.start_date > financial_year_end_date:
            current_year += 1
        else:
            current_year-=1 

        emp_leave_details = LeaveDetails.objects.get(employee=employee,year=current_year)

        leave_details=get_leave_policy_details(employee,current_year)
        floating_holiday_policy = leave_details['allowed_floating_holiday_policy']
        leave_duration = 0
        floating_days = 0
        floating_holidays_used = emp_leave_details.floating_holidays_used
        max_floating_holidays = floating_holiday_policy

        current_date = start_date

        fy_start, fy_end = get_financial_year_dates(request, employee)
        fy_end_extended = fy_end + relativedelta(months=9) # for fetching next years holidays 

        holidays = set(Holiday.objects.filter(date__range=(fy_start, fy_end_extended)).values_list('date', flat=True))
        state_holiday_dates = set(
            StateHoliday.objects.filter(
                state=employee.state,
                date__range=(fy_start, fy_end_extended)
            ).values_list('date', flat=True)
        )
        #combine both 
        holidays |= state_holiday_dates

        floating_holidays = set(FloatingHoliday.objects.filter(date__range=(fy_start, fy_end_extended)).values_list('date', flat=True))
        state_excluded = set(
        StateHoliday.objects.filter(
            country=employee.country,
            date__range=(fy_start, fy_end_extended)
        ).exclude(
            state=employee.state
        ).values_list('date', flat=True)
        )
        # contains both 
        floating_holidays |= state_excluded


        if leave_request.leave_type == 'Floating Leave':
            while current_date <= end_date:
                if current_date.weekday() in [5, 6]:
                    current_date += timedelta(days=1)
                    continue
                if current_date in holidays:
                    current_date += timedelta(days=1)
                    continue
                if current_date in floating_holidays:
                    if floating_holidays_used < max_floating_holidays:
                        floating_days += 1
                        current_date += timedelta(days=1)
                        continue
                leave_duration += 1
                current_date += timedelta(days=1)
        else:
            while current_date <= end_date:
                if current_date.weekday() in [5, 6]:
                    current_date += timedelta(days=1)
                    continue
                if current_date in holidays:
                    current_date += timedelta(days=1)
                    continue
                
                leave_duration += 1
                current_date += timedelta(days=1)

        if action == 'accept':
            leave_request.status = 'Approved'
            if leave_request.leave_type == 'Floating Leave':
                emp_leave_details.planned_float += floating_days
                emp_leave_details.pending_float -= floating_days
                emp_leave_details.save()

            else:
                emp_leave_details.planned_casual += leave_duration
                emp_leave_details.pending_casual -=leave_duration
                emp_leave_details.save()


            
    
    # Email to employee: LEAVE APPROVED
            send_mail(
                subject="Your Leave Request Has Been Approved",
                message=(
                    f"Dear {employee.first_name},\n\n"
                    f"Your leave request from {leave_request.start_date.strftime('%B %d, %Y')} to {leave_request.end_date.strftime('%B %d, %Y')} ({leave_request.leave_type}) "
                    "has been approved.\n\n"
                    "Best regards,\nHR Team"
                ),
                from_email="lms@spectrasoln.com",
                recipient_list=[employee.company_email],
                fail_silently=False,
            )
            
    # Email to PM (if PM email exists): LEAVE APPROVED
    
            send_mail(
                subject=f"Leave Request Approved - {employee.first_name} {employee.last_name}",
                message=(
                    f"Dear Project Manager,\n\n"
                    f"{employee.first_name} {employee.last_name}'s leave request has been approved.\n\n"
                    f"Employee ID: {employee.employee_id}\n"
                    f"Leave Type: {leave_request.leave_type}\n"
                    f"Leave Period: {leave_request.start_date.strftime('%B %d, %Y')} to {leave_request.end_date.strftime('%B %d, %Y')}\n"
                    f"Reason: {leave_request.reason}\n"
                    f"Status: Approved\n\n"
                    f"Please plan accordingly for the employee's absence during this period.\n\n"
                    f"Best regards,\nHR Team"
                ),
                from_email="lms@spectrasoln.com",
                recipient_list=[employee.pm_email],
                fail_silently=False,
            )


        else:
            leave_request.status= "Rejected"


            if leave_request.leave_type == 'Floating Leave':
                emp_leave_details.pending_float -= leave_request.leave_days
            else:
                emp_leave_details.pending_casual -= leave_request.leave_days
            emp_leave_details.save()
    # Email to employee: LEAVE REJECTED
            send_mail(
                subject="Your Leave Request Has Been Rejected",
                message=(
                    f"Dear {employee.first_name},\n\n"
                    f"Your leave request from {leave_request.start_date.strftime('%B %d, %Y')} to {leave_request.end_date.strftime('%B %d, %Y')} ({leave_request.leave_type}) "
                    "has been rejected. For more information, please contact your manager.\n\n"
                    "Best regards,\nHR Team"
                ),
                from_email="lms@spectrasoln.com",
                recipient_list=[employee.company_email],
                fail_silently=False,
            )
            
            # Email to PM (if PM email exists): LEAVE REJECTED
            if employee.pm_email:
                send_mail(
                    subject=f"Leave Request Rejected - {employee.first_name} {employee.last_name}",
                    message=(
                        f"Dear Project Manager,\n\n"
                        f"{employee.first_name} {employee.last_name}'s leave request has been rejected.\n\n"
                        f"Employee ID: {employee.employee_id}\n"
                        f"Leave Type: {leave_request.leave_type}\n"
                        f"Leave Period: {leave_request.start_date.strftime('%B %d, %Y')} to {leave_request.end_date.strftime('%B %d, %Y')}\n"
                        f"Reason: {leave_request.reason}\n"
                        f"Status: Rejected\n\n"
                        f"The employee has been notified of this decision.\n\n"
                        f"Best regards,\nHR Team"
                    ),
                    from_email="lms@spectrasoln.com",
                    recipient_list=[employee.pm_email],
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


    return render(request, 'view_subordinates.html', {
        'employee':manager,
        'subordinates': subordinates,
        'manager': manager,
        'is_manager' : is_manager,
        'emp_id' : manager.employee_id ,
        'emp_fname' : manager.first_name,
        'emp_lname' : manager.last_name,
        'emp_designation' : manager.role.role_name,
        
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
from .utils import get_leave_policy_details



@signin_required
def allocate_leave(request, employee_id):
    manager = get_object_or_404(Employees, user=request.user)
    employee = get_object_or_404(Employees, id=employee_id)
    today = date.today()

    current_year = today.year
    subordinates = Employees.objects.filter(manager=manager)
    is_manager = subordinates.exists()

    # Calculate financial year start and end dates
    financial_year_start, financial_year_end = get_financial_year_dates(request, employee, reference_date=today)
    fy_end_extended = financial_year_end + relativedelta(months=9)

    # Get fixed holidays (exclude floating holidays)
    # regular_holidays = set(Holiday.objects.filter(country=employee.country, year=current_year).values_list('date', flat=True))
    # floating_holiday_dates = set(FloatingHoliday.objects.filter(country=employee.country, year=current_year).values_list('date', flat=True))
    country_holiday_dates = set(
        Holiday.objects.filter(
            country=employee.country,
            date__range=(financial_year_start, fy_end_extended)
        ).values_list('date', flat=True)
    )

    # Dates from state-based holidays
    state_holiday_dates = set(
        StateHoliday.objects.filter(
            state=employee.state,
            date__range=(financial_year_start, fy_end_extended)
        ).values_list('date', flat=True)
    )

    # Combine both sets
    regular_holidays = country_holiday_dates | state_holiday_dates
    floating_holidays = set(
        FloatingHoliday.objects.filter(
            country=employee.country,
            date__range=(financial_year_start, fy_end_extended)
        ).values_list('date', flat=True)
    )

    state_excluded = set(
    StateHoliday.objects.filter(
        country=employee.country,
        date__range=(financial_year_start, fy_end_extended)
    ).exclude(
        state=employee.state
    ).values_list('date', flat=True)
    )

    floating_holiday_dates=floating_holidays | state_excluded


    # --- Calculate LEAVE POLICY ---
    experience_years = (today - employee.enc_valid_from).days // 365 if employee.enc_valid_from else 0


    reset_period = HolidayResetPeriod.objects.filter(country=employee.country).first()
    year_to_use= date.today().year-1 if date.today().month < reset_period.start_month else date.today().year
    policy = HolidayPolicy.objects.filter(country=employee.country, year=year_to_use, min_years_experience__lte=experience_years).order_by('-min_years_experience').first()
    floating_policy = FloatingHolidayPolicy.objects.filter(country=employee.country, year=year_to_use).first()

    employee_leaves=LeaveDetails.objects.filter(employee=employee,year=year_to_use).first()
    if employee_leaves:
        casual_leaves=employee_leaves.total_casual_leaves
    else:
        casual_leaves = (policy.ordinary_holidays_count if policy else 0) + (policy.extra_holidays if policy else 0)

    floating_leaves = floating_policy.allowed_floating_holidays if floating_policy else 0

    def leave_days_agg(qs):
        agg = qs.aggregate(total=Sum('leave_days'))
        return agg['total'] or 0

 

    used_casual_leaves = employee_leaves.casual_leaves_used if employee_leaves else 0
    pending_casual_leaves = employee_leaves.pending_casual if employee_leaves else 0
    planned_casual=employee_leaves.planned_casual if employee_leaves else 0
    used_floating_leaves = employee_leaves.floating_holidays_used if employee_leaves else 0
    pending_floating_leaves = employee_leaves.pending_float if employee_leaves else 0
    planned_float=employee_leaves.planned_float if employee_leaves else 0



    remaining_casual_leaves = casual_leaves - used_casual_leaves - pending_casual_leaves - planned_casual
    remaining_floating_leaves = floating_leaves - used_floating_leaves - pending_floating_leaves -planned_float

    # --- Financial Year Leave Aggregations ---
    leaves_fin_year = LeaveRequest.objects.filter(
        employee_user=employee.user,
        start_date__lte=financial_year_end + relativedelta(months=2),
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
            leave_request=LeaveRequest.objects.create(
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
           
            current_year=date.today().year
            reset_period = HolidayResetPeriod.objects.filter(country=employee.country).first()
            if reset_period:
                start_month = reset_period.start_month
                start_day = reset_period.start_day
                end_month=reset_period.end_month
                end_day=reset_period.end_day
                financial_year_start_date = date(current_year, start_month, start_day)
                financial_year_end_date = date(current_year+1, end_month, end_day)

            if financial_year_start_date <= leave_request.start_date <= financial_year_end_date:
                pass
            elif leave_request.start_date > financial_year_end_date:
                current_year += 1
            else:
                current_year-=1
            leave_details=get_leave_policy_details(employee,current_year)
            holiday_policy = leave_details['allowed_holiday_policy']
            if not holiday_policy:
                messages.error(request,f"No holiday policy configured for the year {current_year} . contact the manager")
                return redirect('request_leave')
            emp_leave_details, created = LeaveDetails.objects.get_or_create(employee=employee,year=current_year,defaults={'total_casual_leaves':holiday_policy})
            if leave_type == "Floating Leave":
                emp_leave_details.planned_float += leave_days
            elif leave_type == "Casual Leave":
                emp_leave_details.planned_casual += leave_days
            emp_leave_details.save()

            send_mail(
                subject="Leave Allocation Notification",
                message=(
                    f"Dear {employee.first_name},\n\n"
                    f"Your manager {manager.first_name} {manager.last_name} "
                    f"has allocated {leave_type} for you from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}.\n\n"
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
        'fy_end_calender': financial_year_end,
        'approved_leaves': approved_leaves,
        'pending_leaves': pending_leaves,
        'rejected_leaves': rejected_leaves,
        'upcoming_leaves': upcoming_leaves,
        'all_leaves': all_leaves,
    }
    return render(request, 'allocate_leave.html', context)

