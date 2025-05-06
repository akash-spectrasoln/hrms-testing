# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from admin_app.models import LeaveRequest
#
# @receiver(post_save, sender=LeaveRequest)
# def send_notification_to_manager(sender, instance, created, **kwargs):
#     if created:  # Only trigger for new leave requests
#         manager = instance.employee_master.employee_manager  # Get the manager
#         if manager and manager.email:  # Ensure manager has an email
#             # Render email content
#             email_html_content = render_to_string(
#                 'leave_request_email.html',
#                 {
#                     'manager_name': manager.name,
#                     'employee_name': instance.employee_master.name,
#                     'start_date': instance.start_date,
#                     'end_date': instance.end_date,
#                     'reason': instance.reason,
#                 }
#             )
#             email_plain_content = strip_tags(email_html_content)
#
#             # Send email
#             send_mail(
#                 subject="New Leave Request Notification",
#                 message=email_plain_content,
#                 from_email="ajaykmani2001@gmail.com",
#                 recipient_list=[manager.email],
#                 html_message=email_html_content,
#             )


from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models.signals import post_save
from django.dispatch import receiver
from admin_app.models import LeaveRequest
#
# @receiver(post_save, sender=LeaveRequest)
# def send_notification_to_manager(sender, instance, created, **kwargs):
#     if created:  # Only trigger for new leave requests
#         manager = instance.employee_master.employee_manager  # Get the manager (employee_manager field)
#         if manager and manager.user.email:  # Ensure the manager has an email (accessing the related User model)
#             # Render email content
#             email_html_content = render_to_string(
#                 'leave_request_email.html',
#                 {
#                     'manager_name': manager.name,  # Access manager's name
#                     'employee_name': instance.employee_master.name,
#                     'start_date': instance.start_date,
#                     'end_date': instance.end_date,
#                     'reason': instance.reason,
#                     'leave_type': instance.get_leave_type_display(),  # Get the display value of leave type
#                     'leave_days': instance.leave_days,  # The calculated leave days
#                 }
#             )
#             email_plain_content = strip_tags(email_html_content)
#
#             # Send email to manager
#             send_mail(
#                 subject="New Leave Request Notification",
#                 message=email_plain_content,
#                 from_email="ajaykmani2001@gmail.com",  # Use the email from your settings
#                 recipient_list=[manager.user.email],  # Access the manager's email through the user
#                 html_message=email_html_content,
#             )

#
import logging

# Create a logger
logger = logging.getLogger(__name__)

@receiver(post_save, sender=LeaveRequest)
def send_notification_to_manager(sender, instance, created, **kwargs):
    if created:
        employee = getattr(instance, 'employee_master', None)
        if not employee:
            logger.warning("LeaveRequest created with no employee_master; skipping manager notification email.")
            return
        manager = getattr(employee, 'manager', None)
        if manager and getattr(manager, 'company_email', None):
            email_html_content = render_to_string(
                'leave_request_email.html',
                {
                    'manager_name': f"{manager.first_name} {manager.last_name}",
                    'employee_name': f"{employee.first_name} {employee.last_name}",
                    'start_date': instance.start_date,
                    'end_date': instance.end_date,
                    'reason': getattr(instance, 'reason', '-'),
                }
            )
            email_plain_content = strip_tags(email_html_content)
            send_mail(
                subject="New Leave Request Notification",
                message=email_plain_content,
                from_email="akashaku32@gmail.com",
                recipient_list=[manager.company_email],
                html_message=email_html_content,
            )


from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models.signals import post_save
from django.dispatch import receiver
from admin_app.models import LeaveRequest

@receiver(post_save, sender=LeaveRequest)
def send_leave_status_update_to_employee(sender, instance, created, **kwargs):
    if not created:  # Triggered only when updating existing leave request
        # Check if the leave request status has changed
        if instance.status in ["Accepted", "Rejected"]:
            employee = instance.employee_master  # Get the employee related to the leave request
            if employee and employee.company_email:  # Ensure employee has an email
                # Render email content
                email_html_content = render_to_string(
                    'leave_status_update_email.html',
                    {
                        'employee_name': f"{employee.first_name} {employee.last_name}",  # Employee's name
                        'leave_type': instance.leave_type,  # Leave type
                        'start_date': instance.start_date,
                        'end_date': instance.end_date,
                        'reason': instance.reason,
                        'status': instance.status,  # Accepted or Rejected
                    }
                )
                email_plain_content = strip_tags(email_html_content)

                # Send email
                send_mail(
                    subject="Your Leave Request Status Update",
                    message=email_plain_content,
                    from_email="akashaku32@gmail.com",
                    recipient_list=[employee.company_email],
                    html_message=email_html_content,
                )


