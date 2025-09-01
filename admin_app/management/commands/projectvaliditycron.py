from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = "Set up daily task to check and deactivate expired projects and assignments."

    def handle(self, *args, **options):
        # 1️⃣ Define crontab: every day at 00:00 AM
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute='*',
            hour='*',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        # 2️⃣ Task details
        task_name = 'Daily Project & Assignment Status Check'
        task_path = 'admin_app.tasks.check_project_and_assignment_status'  

        # 3️⃣ Create or update periodic task
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