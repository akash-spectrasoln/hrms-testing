from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = "Set up daily birthday email task for TODAY's birthdays at 00:00 UTC (5:30 AM IST)."

    def handle(self, *args, **options):
        # Define crontab: every day at 00:00 UTC (5:30 AM IST)
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='0',  # 00:00 UTC = 5:30 AM IST
            day_of_week='*',  # every day
            day_of_month='*',
            month_of_year='*',
        )

        # Unique task name to identify
        task_name = 'Daily Birthday Email Task (Today)'
        task_path = 'admin_app.tasks.send_birthday_emails_today'

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