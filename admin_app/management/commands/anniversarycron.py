from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class Command(BaseCommand):
    help = "Set up periodic task for sending daily work anniversary emails at 1 AM IST."

    def handle(self, *args, **options):
        # Define crontab: every day at 1 AM IST
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='54',
            hour='10',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        # Unique task name
        task_name = 'Daily Work Anniversary Email Task'
        task_path = 'admin_app.tasks.send_anniversary_emails'  # update app name if different

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
            self.stdout.write(self.style.SUCCESS(f"✅ Created periodic task: {task_name}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Updated periodic task: {task_name}"))


