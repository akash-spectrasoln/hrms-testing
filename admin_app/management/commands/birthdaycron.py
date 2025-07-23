from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = "Set up periodic tasks like weekly birthday email sender."

    def handle(self, *args, **options):
        # Define crontab: every Monday at 9 AM
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute='*',
            hour='*',
            day_of_week='3',  # Monday
            day_of_month='*',
            month_of_year='*',
        )

        # Unique task name to identify
        task_name = 'Weekly Birthday Email Task'
        task_path = 'admin_app.tasks.send_birthday_emails'

        # Update if task exists
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
            self.stdout.write(self.style.SUCCESS(f"Created periodic task: {task_name}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated periodic task: {task_name}"))

