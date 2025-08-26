from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = "Set up timesheet reminder tasks: Friday 4PM + Monday 9AM"

    def handle(self, *args, **options):
        # Friday 4PM
        friday_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='16',
            day_of_week='5',  # Friday
            day_of_month='*',
            month_of_year='*'
        )

        PeriodicTask.objects.update_or_create(
            name="Timesheet Reminder Friday 4PM",
            defaults={
                'crontab': friday_schedule,
                'task': 'timesheet.tasks.send_timesheet_reminder',
                'args': json.dumps(['friday']),
                'enabled': True
            }
        )

        # Monday 9AM
        monday_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='9',
            day_of_week='1',  # Monday
            day_of_month='*',
            month_of_year='*'
        )

        PeriodicTask.objects.update_or_create(
            name="Timesheet Reminder Monday 9AM",
            defaults={
                'crontab': monday_schedule,
                'task': 'timesheet.tasks.send_timesheet_reminder',
                'args': json.dumps(['monday']),
                'enabled': True
            }
        )

        self.stdout.write(self.style.SUCCESS("Timesheet reminder tasks created/updated successfully."))
