from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class Command(BaseCommand):
    help = "Send email to manager if subordinates didn't enter timesheet."

    def handle(self, *args, **options):
        # Define crontab: every tuesday at 4 pm IST
        # crontabschedule should be mentioned in UTC
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='30',
            hour='10', 
            day_of_week='2',
            day_of_month='*',
            month_of_year='*',
        )

        # Unique task name
        task_name = 'pending timesheet entry'
        task_path = 'admin_app.tasks.email_to_manager'  # update app name if different

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