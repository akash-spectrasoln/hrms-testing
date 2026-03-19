from celery import shared_task
from .models import Employees, Communication,TimesheetHdr, TimesheetItem,Employees, Holiday, StateHoliday, LeaveRequest,Project,AssignProject
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from datetime import date
from django.db.models import Q
@shared_task
def send_birthday_emails():

    """sends an email to admins listing employees who have birthdays next week (Monday-Sunday)"""
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
    employees = Employees.objects.all().exclude(employee_status="resigned")

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
def send_birthday_emails_today():
    """
    Send birthday notification emails to administrators for employees 
    whose birthday is TODAY.
    """
    # Get today's date
    today = datetime.now().date()

    # Get all users from communication model who should receive the email
    admin_employees = Communication.objects.all()

    # Get all employees to check their birthdays
    employees = Employees.objects.all().exclude(employee_status="resigned")

    # Prepare a list of employees with birthdays TODAY
    employees_with_birthday_today = []

    for employee in employees:
        try:
            # Replace year in DOB to current year for comparison
            dob = employee.enc_date_of_birth.replace(year=today.year)

            # Check if the birthday is TODAY
            if dob == today:
                employees_with_birthday_today.append({
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "birth_day_date": dob
                })
        except:
            # Skip employees with invalid DOB or error in date conversion
            pass

    if employees_with_birthday_today:
        for admin in admin_employees:
            subject = "Employee Birthday Today!"

            # Plain text fallback
            plain_message = f"Hi {admin.user.first_name},\n\nPlease view this email in HTML format to see today's birthday celebrants.\n\nBest regards,\nYour Leave Management System"

            # HTML content
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <p>Hi {admin.user.first_name},</p>
                <p>🎉 The following employee(s) are celebrating their birthday <strong>TODAY</strong>:</p>
                
                <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 80%;">
                    <thead style="background-color: #f2f2f2;">
                        <tr>
                            <th align="left">Name</th>
                            <th align="left">Date</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for emp in employees_with_birthday_today:
                formatted_date = emp['birth_day_date'].strftime('%B %d, %Y')
                html_message += f"""
                    <tr>
                        <td>{emp['first_name']} {emp['last_name']}</td>
                        <td>{formatted_date}</td>
                    </tr>
                """

            html_message += """
                    </tbody>
                </table>

                <p style="margin-top: 20px;">Don't forget to wish them a happy birthday! 🎈</p>
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
    employees = Employees.objects.all().exclude(employee_status="resigned")

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




import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task
def send_timesheet_reminder(day_type="monday_morning", country_id=None):
    """
    Send reminder emails to employees with incomplete timesheets.
    Runs on Monday 10 AM (monday_morning) and Monday 5 PM (monday_evening) for previous week.
    Logs detailed processing steps for each employee.
    """
    today = timezone.localdate()
    logger.info("Task started for day_type=%s, country_id=%s", day_type, country_id)

    # Calculate week range (Sunday → Saturday) - both reminders are for previous week
    if day_type.lower() == "monday_morning":
        week_start = today - timedelta(days=today.weekday() + 8)  # previous Sunday
        week_end = week_start + timedelta(days=6)
        message_text = f"It is time to submit your timesheet for the week {week_start} to {week_end}."
    elif day_type.lower() == "monday_evening":
        week_start = today - timedelta(days=today.weekday() + 8)  # previous Sunday
        week_end = week_start + timedelta(days=6)
        message_text = f"Your timesheet is delayed. Friendly reminder: Please Submit your timesheet for the last week {week_start} to {week_end}."
    else:
        logger.error("Invalid day_type provided: %s", day_type)
        return

    logger.info("Week calculated: %s → %s", week_start, week_end)

    # Filter active employees (exclude contractors + excl_folup upfront)
    employees = (
        Employees.objects.filter(is_deleted=False, user__is_active=True)
        .exclude(employee_type__code="C")
        .exclude(excl_folup=True)
        .exclude(employee_status="resigned")
        .exclude(excl_TSheet=True)
    )
    if country_id:
        employees = employees.filter(country_id=country_id)

    logger.info("Total employees to process: %s", employees.count())

    for emp in employees:
        try:
            logger.info("Processing employee: %s (%s)", emp.first_name, emp.id)

            min_daily_hours = getattr(emp.country, "working_hours", 9) or 9
            weekly_threshold = min_daily_hours * 5
            logger.debug(
                "Employee %s: min_daily_hours=%s, weekly_threshold=%s",
                emp.first_name, min_daily_hours, weekly_threshold
            )

            # Collect holidays for employee’s country
            emp_holidays = set(
                Holiday.objects.filter(
                    date__range=(week_start, week_end),
                    country=emp.country
                ).values_list("date", flat=True)
            )
            emp_holidays |= set(
                StateHoliday.objects.filter(
                    date__range=(week_start, week_end),
                    state__country=emp.country
                ).values_list("date", flat=True)
            )
            logger.debug("Employee %s holidays: %s", emp.first_name, sorted(emp_holidays))

            # Collect leave days
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
                    leave_days.add(start + timedelta(days=i))
            logger.debug("Employee %s leave days: %s", emp.first_name, sorted(leave_days))

            # Get timesheet entries
            ts_hdr = TimesheetHdr.objects.filter(employee=emp, week_start=week_start).first()
            timesheet_items = list(
                ts_hdr.timesheet_items.filter(wrk_date__range=(week_start, week_end))
            ) if ts_hdr else []
            logger.debug("Employee %s has %s timesheet entries", emp.first_name, len(timesheet_items))

            # Map entered hours per date
            entered_by_date = {}
            for item in timesheet_items:
                entered_by_date[item.wrk_date] = entered_by_date.get(item.wrk_date, 0) + item.wrk_hours

            total_hours = 0
            can_approve = True
            all_days = [week_start + timedelta(days=i) for i in range(7)]

            for current_date in all_days:
                entered_hours = entered_by_date.get(current_date, 0)

                if entered_hours > 0:
                    logger.debug(
                        "Employee %s entered %s hours on %s",
                        emp.first_name, entered_hours, current_date
                    )
                    if entered_hours < min_daily_hours:
                        logger.info(
                            "Employee %s failed daily minimum hours on %s (%s < %s)",
                            emp.first_name, current_date, entered_hours, min_daily_hours
                        )
                        can_approve = False
                    total_hours += entered_hours
                else:
                    if current_date in leave_days or current_date in emp_holidays:
                        total_hours += min_daily_hours
                        logger.debug(
                            "Employee %s auto-filled %s hours for leave/holiday on %s",
                            emp.first_name, min_daily_hours, current_date
                        )
                    else:
                        logger.debug(
                            "Employee %s missing entry on %s (0 hours)",
                            emp.first_name, current_date
                        )

            # Skip if full leave/holiday week
            working_weekdays = [d for d in all_days if d.weekday() < 5]
            if all(d in leave_days or d in emp_holidays for d in working_weekdays):
                logger.info("Skipping %s (full leave/holiday week)", emp.first_name)
                continue

            # Weekly threshold check
            if total_hours < weekly_threshold:
                logger.info(
                    "Employee %s failed weekly threshold: %s < %s",
                    emp.first_name, total_hours, weekly_threshold
                )
                can_approve = False
            else:
                logger.info(
                    "Employee %s passes weekly threshold: %s >= %s",
                    emp.first_name, total_hours, weekly_threshold
                )

            # Send email if required
            if not can_approve:
                subject = "Timesheet Reminder"
                plain_message = f"Dear {emp.first_name},\n\n{message_text}\n\nBest regards,\nSpectra HR Team"
                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color:#333333; line-height:1.6; font-weight: normal;">
                <div style="max-width:600px; margin:0; padding:20px; border:1px solid #ddd; border-radius:8px; background:#fafafa;">
                    <p>Dear {emp.first_name},</p>
                    <p>{message_text}</p>
                    <p style="margin:15px 0; padding:10px 0 10px 2px ; background:#f0f8ff; border-left:4px solid #0073e6;">
                        Week: {week_start} to {week_end}
                    </p>
                    <p>Best regards,<br>Spectra HR Team</p>
                </div>
                </body>
                </html>
                """
                logger.info("Sending email to %s (%s) with subject='%s'", emp.first_name, emp.company_email, subject)
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [emp.company_email],
                    html_message=html_message,
                    fail_silently=False,
                )
                logger.info("Email successfully sent to %s (%s)", emp.first_name, emp.company_email)
            else:
                logger.info("No email required for %s (all conditions met)", emp.first_name)

        except Exception as e:
            logger.exception("Error processing employee %s: %s", emp.first_name, e)
            continue

    logger.info(
        "Timesheet reminder task completed for day_type=%s, country_id=%s",
        day_type, country_id
    )

from django.db.models import Count
from timesheet_app.views import get_week_start_end

@shared_task
def send_pendingtimesheet_emails():

    """
    sending emails to the manager if there is any timesheet pending to be approved
    """

    managers = Employees.objects.annotate(num_reports=Count('employees_managed')).filter(num_reports__gt=0,employee_status="employed")


    for manager in managers:

        subordinates = manager.employees_managed.all().exclude(excl_TSheet=True)

        today = datetime.now().date()

        # Find this week's Sunday
        current_week_start = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today

        # Previous week's Saturday
        cutoff_week_end = current_week_start - timedelta(days=1)

        #checking any timesheets pending for approval till previous week
        pending_timesheets = TimesheetHdr.objects.filter(employee__in=subordinates,week_end__lte=cutoff_week_end,is_approved=False).order_by("week_start")

        if pending_timesheets.exists():
            total_count = pending_timesheets.count()

            subject = "Pending Timesheet Approvals"

            message_text = (
                f"You have {total_count} pending timesheet(s) "
            )

            plain_message = (
                f"Dear {manager.first_name},\n\n"
                f"{message_text}\n\n"
                f"Please review them at your earliest convenience.\n\n"
                f"Best regards,\nSpectra HR Team"
            )

            # HTML version
            week_html = ""
            for ts in pending_timesheets:
                week_html += f"""
                    <li>
                        {ts.employee.first_name} {ts.employee.last_name} : {ts.week_start} to {ts.week_end}
                    </li>
                """
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color:#333;">
                <div style="max-width:600px; padding:20px;
                            border:1px solid #ddd; border-radius:8px; background:#fafafa;">

                    <p>Dear {manager.first_name},</p>

                    <p>You have <strong>{total_count}</strong>
                    pending timesheet(s) waiting for approval:</p>

                    <ul>
                        {week_html}
                    </ul>

                    <p>Please review them at your earliest convenience.</p>

                    <p>Best regards,<br>Spectra HR Team</p>
                </div>
            </body>
            </html>
            """
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [manager.company_email],
                html_message=html_message,
                fail_silently=False,
            )

@shared_task    
def email_to_manager():
    """
    Send email to manager if subordinates didn't enter timesheet
    (excluding holidays, state holidays, and leave days)
    """

    today = datetime.now().date()

    current_week_start = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today  # sunday

    duration_week_start = current_week_start - timedelta(days=28)
    duration_week_end = current_week_start - timedelta(days=1)
    
    # fetching managers
    managers = Employees.objects.annotate(num_reports=Count('employees_managed')).filter(num_reports__gt=0,employee_status="employed")

    for manager in managers:

        # fetching subordinates excluding resigned employees (if resignation date is on previous week then included)
        subordinates = manager.employees_managed.filter(Q(resignation_date__isnull=True) | Q(resignation_date__gte=duration_week_start),excl_TSheet=False)

        not_entered=[]
        for emp in subordinates:


            emp_holidays = set(
                Holiday.objects.filter(
                    date__range=(duration_week_start,duration_week_end),
                    country=emp.country
                ).values_list("date", flat=True)
            )      
            emp_holidays |= set(
                StateHoliday.objects.filter(
                    date__range=(duration_week_start,duration_week_end),
                    state=emp.state
                ).values_list("date", flat=True)
            ) 
            # Collect leave days
            leave_days = set()
            leaves = LeaveRequest.objects.filter(
                employee_master=emp,
                status="Approved",
                start_date__lte=duration_week_end,
                end_date__gte=duration_week_start,
            )
            for leave in leaves:
                start = max(leave.start_date, duration_week_start)
                end = min(leave.end_date, duration_week_end)
                for i in range((end - start).days + 1):
                    leave_days.add(start + timedelta(days=i))
            

            # Compute working days once
            working_days = []
            d = duration_week_start

            while d <= duration_week_end:
                if d.weekday() < 5:
                    working_days.append(d)
                d += timedelta(days=1)

            # filtering only the working days in a week by excluding holidays and leaves
            # if no timesheet entry is done on a working day then it is notified to the manager
            for date in working_days:

                # checks if the date(working day in a week)
                if emp.resignation_date and date > emp.resignation_date:
                    break
                if date in leave_days or date in emp_holidays:
                    continue  # skip holidays and leave days

                # ts_hdr.timesheet_items fetches the per day timesheet entries of ts_hdr record
                if not TimesheetItem.objects.filter(hdr__employee_id=emp.id,wrk_date=date).exists():
                    not_entered.append(f"{emp.first_name} {emp.last_name}:{date}")

        # Send email if any missing timesheet
        if not_entered:
            subject = "Subordinates Timesheet Pending"
            plain_message = (
                f"Dear {manager.first_name},\n\n"
                f"The following team members have missing timesheet entries "
                f"for the period {duration_week_start} to {duration_week_end}.\n\n"
                f"Missing Timesheet Entry Dates:\n"
                + "\n".join(not_entered) +
                "\n\nPlease ensure the timesheets are completed at the earliest.\n\n"
                f"Best regards,\nSpectra HR Team"
            )

            week_html = "".join([f"<li>{ts}</li>" for ts in not_entered])
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color:#333;">
                <div style="max-width:600px; padding:20px; border:1px solid #ddd; border-radius:8px; background:#fafafa;">
                    <p>Dear {manager.first_name},</p>
                    <p>
                        The following team members have missing timesheet entries 
                        for the timeperiod <strong>{duration_week_start} to {duration_week_end}</strong>.
                    </p>

                    <p><strong>Missing Timesheet Entry Dates:</strong></p>
                    <ul>
                        {week_html}
                    </ul>
                    <p>Please ensure the timesheets are completed at the earliest.</p>
                    <p>Best regards,<br>Spectra HR Team</p>
                </div>
            </body>
            </html>
            """
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [manager.company_email],
                html_message=html_message,
                fail_silently=False,
            )


@shared_task
def delayed_timesheet_entry():
    """
    Send email to employee if they have delayed timesheet entries
    in the previous month.

    """

    today = timezone.now().date()

    # First day of current month
    first_day_current_month = today.replace(day=1)

    # Last day of previous month
    last_day_previous_month = first_day_current_month - timedelta(days=1)

    # First day of previous month
    first_day_previous_month = last_day_previous_month.replace(day=1)

    employees = Employees.objects.all().exclude(Q(employee_status="resigned") | Q(excl_folup=True) | Q(excl_TSheet=True))

    for emp in employees:
        delayed_entries = TimesheetHdr.objects.filter(
            employee=emp,
            is_delayed=True,
            week_start__lte=last_day_previous_month,
            week_end__gte=first_day_previous_month
        ).order_by("week_start")

        if delayed_entries.exists():
            subject = "Delayed Timesheet Entry"

            week_html=""
            for entry in delayed_entries:
                week_html+=f"""
                <li>
                    {entry.week_start} to {entry.week_end}
                </li>
                """


            plain_message = (
                f"Dear {emp.first_name},\n\n"
                f"You have delayed timesheet entries for the month "
                f"{first_day_previous_month.strftime('%B %Y')}.\n\n"
                f"Please try to update your timesheet on time.\n\n"
                f"Best regards,\n"
                f"Spectra HR Team"
            )

            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color:#333;">
                <div style="max-width:600px; padding:20px; border:1px solid #ddd; border-radius:8px; background:#fafafa;">
                    <p>Dear {emp.first_name},</p>
                    <p>
                        You have <strong>{delayed_entries.count()} delayed timesheet entries</strong> 
                        for <strong>{first_day_previous_month.strftime('%B %Y')}</strong> on weeks:
                    </p>
                    <ul>
                        {week_html}
                    </ul>
                    <p>Please try to update your timesheet on time.</p>
                    <p>Best regards,<br>Spectra HR Team</p>
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
