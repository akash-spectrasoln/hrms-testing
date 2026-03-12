from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class Command(BaseCommand):
    help = "Send email to employee if they have delayed timesheet entries in the previous month."

    def handle(self, *args, **options):
        # Define crontab: First Wednesday of every month at 04:30 UTC = 10:00 am IST
        # crontabschedule should be mentioned in UTC
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='30',
            hour='4', 
            day_of_week='3',
            day_of_month='1-7', # first week of every month
            month_of_year='*',
        )

        # Unique task name
        task_name = 'delayed timesheet entry'
        task_path = 'admin_app.tasks.delayed_timesheet_entry'  # update app name if different

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