from celery import shared_task
from .models import Employees, Communication,TimesheetHdr, Employees, Holiday, StateHoliday, LeaveRequest,Project,AssignProject
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from datetime import date
from django.db.models import Q
@shared_task
def send_birthday_emails():
    # Get today's date
    today = datetime.now().date()

    # Calculate how many days until the next Monday
    days_until_monday = 7 - today.weekday()
    if days_until_monday == 0:
        days_until_monday = 7 # If today is Monday, go to next week's Monday

    # Calculate the start (Monday) and end (Sunday) of the upcoming week 
    next_monday = today + timedelta(days=days_until_monday)
    next_sunday = next_monday + timedelta(days=6)

    # Get all users from communication model who should receive the email
    admin_employees = Communication.objects.all()

    # Get all employees to check their birthdays
    employees = Employees.objects.all()

    # Prepare a list of employees with birthdays in the next week
    employees_with_birthday = []

    for employee in employees:
        try:
            # Replace year in DOB to current year for comparison
            dob = employee.enc_date_of_birth.replace(year=next_monday.year)

            # Check if the birthday falls within next Monday to Sunday
            if next_monday <= dob <= next_sunday:
                employees_with_birthday.append({
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "birth_day_date": dob
                })
        except:

            # Skip employees with invalid DOB or error in date conversion
            pass

    if employees_with_birthday:

        # Sort employees by birthday date
        employees_with_birthday.sort(key=lambda x: x['birth_day_date'])

        for admin in admin_employees:
                
            subject = "🎉 Upcoming Employee Birthdays (Next Week)"

            # Plain text fallback (still needed for compatibility)
            plain_message = f"Hi {admin.user.first_name},\n\nPlease view this email in HTML format to see the birthday table.\n\nBest regards,\nYour Leave Management System"

            # HTML content is used for adding table for the list
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <p>Hi {admin.user.first_name},</p>
                <p>The following employees have birthdays next week:</p>
                
                <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 80%;">
                    <thead style="background-color: #f2f2f2;">
                        <tr>
                            <th align="left">Date</th>
                            <th align="left">Name</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for emp in employees_with_birthday:
                formatted_date = emp['birth_day_date'].strftime('%B %d (%a)')
                html_message += f"""
                    <tr>
                        <td>{formatted_date}</td>
                        <td>{emp['first_name']} {emp['last_name']}</td>
                    </tr>
                """

            html_message += """
                    </tbody>
                </table>

                <p style="margin-top: 20px;">Best regards,<br>Your LMS</p>
            </body>
            </html>
            """

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin.user.email],
                html_message=html_message,
                fail_silently=False
            )


@shared_task
def send_anniversary_emails():
    """
    Send congratulatory emails to employees on their work anniversary.
    Anniversary is based on the `valid_from` field in Employees model.
    """
    today = datetime.now().date()

    # Get all employees
    employees = Employees.objects.all()

    for employee in employees:
        try:
            if employee.enc_valid_from:  # make sure the date is not None
                # Check if today matches the employee's valid_from (ignoring year)
                if employee.enc_valid_from.month == today.month and employee.enc_valid_from.day == today.day:

                    subject = "Your Service"

                    # Plain text fallback
                    plain_message = (
                        f"Dear {employee.first_name},\n\n"
                        f"Congratulations on the anniversary of your first day at Spectra! "
                        f"The dedication, innovative ideas, and great collaboration that you and your colleagues across Spectra show daily is truly inspiring. "
                        f"Thank you for everything you do for Spectra!\n\n"
                        f"All the best,\nDiana"
                    )

                    # HTML message
                    html_message = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; color: #333;">
                        <p>Dear {employee.first_name},</p>
                        <p><span>Congratula&#173;tions</span> on the anniversary of your first day at Spectra!</p>
                        <p>
                            The dedication, innovative ideas, and great collaboration that you and your colleagues
                            across Spectra show daily is truly inspiring.
                        </p>
                        <p>Thank you for everything you do for Spectra!</p>

                        <p style="margin-top: 20px;">All the best,<br>Diana</p>
                    </body>
                    </html>
                    """

                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[employee.company_email],  # ensure Employees model has email field
                        html_message=html_message,
                        fail_silently=False
                    )

        except Exception as e:
            # Skip employees with invalid data
            print(f"Error processing employee {employee.id}: {e}")
            continue


import logging

logger = logging.getLogger(__name__)

@shared_task
def check_project_and_assignment_status():
    """
    Checks the valid_to and end_date of projects and assignments
    and deactivates them if they have expired.
    This task is designed to be run daily.
    """

    today = date.today()

    # -----------------------------------------------------------
    # Task 1: Deactivate expired projects
    # -----------------------------------------------------------
    expired_projects_q = Q(is_active=True) & (Q(valid_to__lt=today) | Q(valid_from__gt=today))
    updated_projects = Project.objects.filter(expired_projects_q).update(is_active=False)
    logger.info(f"Deactivated {updated_projects} expired projects.")

    # -----------------------------------------------------------
    # Task 2: Deactivate expired project assignments
    # -----------------------------------------------------------
    expired_assignments_q = Q(is_active=True) & (Q(end_date__lt=today) | Q(start_date__gt=today))
    updated_assignments = AssignProject.objects.filter(expired_assignments_q).update(is_active=False)
    logger.info(f"Deactivated {updated_assignments} expired project assignments.")


from django.db.models import Sum, Q

from django.utils import timezone
@shared_task
def send_timesheet_reminder(day_type='friday'):
    """
    day_type: 'friday' or 'monday'
    - Friday: Check current week
    - Monday: Check previous week
    Sends a reminder email to employees with incomplete timesheets.
    """

    today = timezone.localdate()
    
    if day_type == 'friday':
        # Current week (Monday-Sunday)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        logger.info(f"[Friday Reminder] Checking timesheets for {week_start} to {week_end}")
    elif day_type == 'monday':
        # Previous week
        week_start = today - timedelta(days=today.weekday() + 7)
        week_end = week_start + timedelta(days=6)
        logger.info(f"[Monday Reminder] Checking timesheets for {week_start} to {week_end}")
    else:
        logger.warning(f"Invalid day_type: {day_type}")
        return

    employees = Employees.objects.filter(is_active=True, user__is_active=True)

    for emp in employees:
        try:
            # --- Fetch holidays and leave days ---
            holidays = set(Holiday.objects.filter(
                country=emp.country, date__range=(week_start, week_end)
            ).values_list('date', flat=True)) | set(StateHoliday.objects.filter(
                country=emp.country, state=emp.state, date__range=(week_start, week_end)
            ).values_list('date', flat=True))

            leave_days = set()
            for leave in LeaveRequest.objects.filter(
                employee_master=emp,
                status='Approved',
                start_date__lte=week_end,
                end_date__gte=week_start
            ):
                for d in range((leave.end_date - leave.start_date).days + 1):
                    day = leave.start_date + timedelta(days=d)
                    if day.weekday() < 5 and day not in holidays:
                        leave_days.add(day)

            # --- Check if employee is fully exempt ---
            working_days = [week_start + timedelta(days=i) for i in range(5)]
            working_days = [d for d in working_days if d not in holidays and d not in leave_days]
            if not working_days:
                continue  # Fully exempt

            # --- Fetch or create timesheet header ---
            ts_hdr = TimesheetHdr.objects.filter(employee=emp, week_start=week_start).first()
            incomplete = False

            if not ts_hdr:
                incomplete = True
            else:
                min_hours = getattr(emp.country, 'working_hours', 9) or 9
                for day in working_days:
                    total_hours = ts_hdr.timesheet_items.filter(wrk_date=day).aggregate(
                        total=Sum('wrk_hours')
                    )['total'] or 0
                    if total_hours < min_hours:
                        incomplete = True
                        break

            if incomplete:
                # --- Send reminder email ---
                subject = f"Reminder: Timesheet Incomplete ({week_start} to {week_end})"
                message = f"Hello {emp.first_name},\n\nPlease submit your timesheet for the week {week_start} to {week_end}.\n\nBest regards,\nYour LMS"
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    ['rtgpes2020@gmail.com'],
                    fail_silently=False
                )
                logger.info(f"Sent reminder to {'rtgpes2020@gmail.com'} for week {week_start} - {week_end}")

        except Exception as e:
            logger.error(f"Error checking timesheet for {emp.first_name} ({emp.employee_id}): {e}")

    logger.info("Timesheet reminder task finished.")