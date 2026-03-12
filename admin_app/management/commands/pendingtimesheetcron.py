from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class Command(BaseCommand):
    help = "Set up periodic task for sending emails to manager if any pending timesheet approvals."

    def handle(self, *args, **options):
        # Define crontab: every wednesday 9 am IST
        # crontabschedule should be mentioned in UTC
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='30',
            hour='3', 
            day_of_week='3',
            day_of_month='*',
            month_of_year='*',
        ) 

        # Unique task name
        task_name = 'pending timesheet approvals'
        task_path = 'admin_app.tasks.send_pendingtimesheet_emails'  # update app name if different

        # Create or update the periodic task
        task, created = PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                'crontab': schedule,
                'task': task_path,
                'args': json.dumps([]),
                'enabled': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f" Created periodic task: {task_name}"))
        else:
            self.stdout.write(self.style.SUCCESS(f" Updated periodic task: {task_name}"))