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
    Daily task to:
    1️⃣ Deactivate expired projects/assignments.
    2️⃣ Activate projects/assignments that are currently valid.
    """

    today = timezone.now().date()  # timezone-aware current date

    # -----------------------------------------------------------
    # Projects
    # -----------------------------------------------------------
    # Deactivate expired or not-yet-started projects
    expired_projects_q = Q(is_active=True) & (Q(valid_to__lt=today) | Q(valid_from__gt=today))
    Project.objects.filter(expired_projects_q).update(is_active=False)

    # Activate current projects
    active_projects_q = Q(is_active=False) & Q(valid_from__lte=today) & Q(valid_to__gte=today)
    Project.objects.filter(active_projects_q).update(is_active=True)

    # -----------------------------------------------------------
    # Project Assignments
    # -----------------------------------------------------------
    # Deactivate expired or not-yet-started assignments
    expired_assignments_q = Q(is_active=True) & (Q(end_date__lt=today) | Q(start_date__gt=today))
    AssignProject.objects.filter(expired_assignments_q).update(is_active=False)

    # Activate current assignments
    active_assignments_q = Q(is_active=False) & Q(start_date__lte=today) & Q(end_date__gte=today)
    AssignProject.objects.filter(active_assignments_q).update(is_active=True)

from django.utils import timezone
from django.db.models import Sum, Q

@shared_task
def send_timesheet_reminder(day_type="friday", country_id=None):
    """
    Send reminder emails to employees with incomplete timesheets.
    Works for Monday and Friday separately.
    """

    today = timezone.localdate()

    # Determine week range based on the day_type
    if day_type.lower() == "friday":
        # Current week: Monday → Sunday
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        message_text = f"It is time to submit your timesheet for the week {week_start} to {week_end}."
    elif day_type.lower() == "monday":
        # Previous week: Monday → Sunday
        week_start = today - timedelta(days=today.weekday() + 7)
        week_end = week_start + timedelta(days=6)
        message_text = f"Friendly reminder: submit your timesheet for last week {week_start} to {week_end}."
    else:
        logger.error("Invalid day_type provided: %s", day_type)
        return

    # Filter active employees
    employees = Employees.objects.filter(is_deleted=False, user__is_active=True)
    if country_id:
        employees = employees.filter(country_id=country_id)

    logger.info("Processing employees (country %s): %s", country_id, employees.count())

    # Collect holidays
    holidays = set(Holiday.objects.filter(date__range=(week_start, week_end)).values_list("date", flat=True))
    holidays |= set(StateHoliday.objects.filter(date__range=(week_start, week_end)).values_list("date", flat=True))

    for emp in employees:
        try:
            # Determine leave days
            leave_days = set()
            leaves = LeaveRequest.objects.filter(
                employee_master=emp,
                status="Approved",
                start_date__lte=week_end,
                end_date__gte=week_start,
            )
            for leave in leaves:
                start = max(leave.start_date, week_start)
                end = min(leave.end_date, week_end)
                for i in range((end - start).days + 1):
                    day = start + timedelta(days=i)
                    # Only weekdays count
                    if day.weekday() < 5:
                        leave_days.add(day)

            # Determine working days: Mon-Fri excluding leave & holidays
            working_days = [
                week_start + timedelta(days=i) 
                for i in range(5)  # Only Monday → Friday
                if (week_start + timedelta(days=i)) not in holidays
                and (week_start + timedelta(days=i)) not in leave_days
            ]

            if not working_days:
                logger.debug("Skipping %s, no working days left", emp.first_name)
                continue

            # Get timesheet header for the week
            ts_hdr = TimesheetHdr.objects.filter(employee=emp, week_start=week_start).first()
            incomplete = False
            min_hours = getattr(emp.country, "working_hours", 9) or 9

            if not ts_hdr:
                incomplete = True
                logger.debug("No timesheet found for %s", emp.first_name)
            else:
                # Check each working day
                for day in working_days:
                    total_hours = ts_hdr.timesheet_items.filter(wrk_date=day).aggregate(total=Sum("wrk_hours"))["total"] or 0
                    if total_hours < min_hours:
                        incomplete = True
                        break

            # Send email if incomplete
            if incomplete:
                subject = "Timesheet Reminder"
                plain_message = f"Dear {emp.first_name},\n\n{message_text}\n\nBest regards,\nSpectra HR Team"
                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color:#333333; line-height:1.6; font-weight: normal;">
                <div style="max-width:600px; margin:0; padding:20px; border:1px solid #ddd; border-radius:8px; background:#fafafa;">

                    <!-- Greeting -->
                    <p style="font-weight: normal;">
                    Dear <span style="font-weight: normal;">{emp.first_name}</span>,
                    </p>

                    <!-- Main message -->
                    <p style="font-weight: normal;">{message_text}</p>

                    <!-- Week block -->
                    <p style="margin:15px 0; padding:10px; background:#f0f8ff; border-left:4px solid #0073e6; font-weight: normal;">
                    <span style="font-weight: normal;">Wee&#8203;k&#58;</span> {week_start} to {week_end}
                    </p>

                    <!-- Footer -->
                    <p style="font-weight: normal;">
                    Best regards,<br>
                    <span style="font-weight: normal;">Spectra&nbsp;HR&nbsp;Te&#8203;am</span>
                    </p>

                </div>
                </body>
                </html>
                """




                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [emp.company_email],
                    html_message=html_message,
                    fail_silently=False,
                )
                logger.info("Reminder sent to %s", emp.first_name)

        except Exception as e:
            logger.exception("Error processing %s: %s", emp.first_name, e)
            continue
