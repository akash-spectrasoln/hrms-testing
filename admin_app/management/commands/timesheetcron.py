from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = "Set up timesheet reminder tasks: Friday 4PM + Monday 9AM"

    def handle(self, *args, **options):
        # --- Friday 4PM schedule ---
        friday_schedule, created = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='16',          # 4 PM
            day_of_week='5',    # Friday
            day_of_month='*',
            month_of_year='*'
        )
        if created:
            self.stdout.write("Created Friday 4PM crontab schedule.")

        PeriodicTask.objects.update_or_create(
            name="Timesheet Reminder Friday 4PM",
            defaults={
                'crontab': friday_schedule,
                'task': 'admin_app.tasks.send_timesheet_reminder',
                'args': json.dumps(['friday']),
                'enabled': True
            }
        )
        self.stdout.write(self.style.SUCCESS("Friday 4PM reminder task created/updated."))

        # --- Monday 9AM schedule ---
        monday_schedule, created = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='9',           # 9 AM
            day_of_week='1',    # Monday
            day_of_month='*',
            month_of_year='*'
        )
        if created:
            self.stdout.write("Created Monday 9AM crontab schedule.")

        PeriodicTask.objects.update_or_create(
            name="Timesheet Reminder Monday 9AM",
            defaults={
                'crontab': monday_schedule,
                'task': 'admin_app.tasks.send_timesheet_reminder',
                'args': json.dumps(['monday']),
                'enabled': True
            }
        )
        self.stdout.write(self.style.SUCCESS("Monday 9AM reminder task created/updated."))

        # --- Optional: Every-minute test schedule (for testing only) ---
        test_schedule, created = CrontabSchedule.objects.get_or_create(
            minute='*',
            hour='*',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )
        PeriodicTask.objects.update_or_create(
            name="Timesheet Reminder Test Every Minute",
            defaults={
                'crontab': test_schedule,
                'task': 'admin_app.tasks.send_timesheet_reminder',
                'args': json.dumps(['friday']),
                'enabled': True
            }
        )
        self.stdout.write(self.style.SUCCESS("Every-minute test reminder task created (for testing only)."))

        self.stdout.write(self.style.SUCCESS("✅ Timesheet reminder tasks setup completed successfully."))
