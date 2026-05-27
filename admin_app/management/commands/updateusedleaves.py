from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class Command(BaseCommand):
    help = "registering the background job to update the used leaves count of all employees"

    def handle(self, *args, **options):
        # Define crontab:  every day at 18:35 UTC = 12:05 am IST
        # crontabschedule should be mentioned in UTC
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='35',
            hour='18', 
            day_of_week='*',
            day_of_month='*', 
            month_of_year='*',
        )

        # Unique task name
        task_name = 'update used leaves count'
        task_path = 'admin_app.tasks.update_used_leaves'  # update app name if different

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