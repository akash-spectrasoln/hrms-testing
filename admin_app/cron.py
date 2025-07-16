import logging
from django_cron import CronJobBase, Schedule
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Employees,User


class BirthdayEmailCronJob(CronJobBase):
    schedule = Schedule(run_every_mins=1)  # 🔁 Run every 5 minutes
    code = 'admin_app.birthday_email_cron'
    def do(self):

        #get next  week range from monday to sunday
        today=datetime.now().date()
        days_until_monday = 7 - today.weekday()
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday=today + timedelta(days=days_until_monday)
        next_sunday=next_monday + timedelta(days=6)
        print(next_monday,next_sunday,"{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}")

        admin_employees = User.objects.filter(is_superuser=True)
        employees=Employees.objects.all()

        
        employees_with_birthday=[]

        #checking employees within the week range
        for employee in employees:
            
            try:

                #dob of employee is changed with current year 
                dob=employee.enc_date_of_birth.replace(year=next_monday.year)
                if next_monday <= dob <= next_sunday:
                    employees_with_birthday.append({"first_name":employee.first_name,
                                                    "last_name":employee.last_name,
                                                    "birth_day_date":dob})
                    
            except Exception as e:
                #making this bug free
                pass

        print(employees_with_birthday,"]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]")
        if employees_with_birthday :
            employees_with_birthday.sort(key=lambda x: x['birth_day_date'])

            for admin in admin_employees:
                subject = "🎉 Upcoming Employee Birthdays (Next Week)"

                # Plain text fallback (still needed for compatibility)
                plain_message = f"Hi {admin.first_name},\n\nPlease view this email in HTML format to see the birthday table.\n\nBest regards,\nYour Leave Management System"

                # HTML content
                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <p>Hi {admin.first_name},</p>
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

                    <p style="margin-top: 20px;">Best regards,<br>Your Leave Management System</p>
                </body>
                </html>
                """

                send_mail(
                    subject=subject,
                    message=plain_message,  # fallback text
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin.email],
                    html_message=html_message,
                    fail_silently=False
                )

            


