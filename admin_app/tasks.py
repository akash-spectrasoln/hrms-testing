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

from django.utils import timezone
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


