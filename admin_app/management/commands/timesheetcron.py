from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = "Set up timesheet reminder tasks for India & US employees (UTC schedule)"

    def handle(self, *args, **options):
        # UTC times corresponding to local times:
        # India 4 PM IST → 10:30 AM UTC
        # US 5 PM ET → 9 PM UTC
        schedules = [
            # Friday
            {
                "name": "Timesheet Reminder Friday India",
                "hour": "10",
                "minute": "30",
                "day_of_week": "5",
                "timezone": "UTC",
                "args": ["friday", 1],  # India
            },
            {
                "name": "Timesheet Reminder Friday US",
                "hour": "21",
                "minute": "0",
                "day_of_week": "5",
                "timezone": "UTC",
                "args": ["friday", 2],  # US
            },
            # Monday
            {
                "name": "Timesheet Reminder Monday India",
                "hour": "3",
                "minute": "30",
                "day_of_week": "1",
                "timezone": "UTC",
                "args": ["monday", 1],
            },
            {
                "name": "Timesheet Reminder Monday US",
                "hour": "13",
                "minute": "0",
                "day_of_week": "1",
                "timezone": "UTC",
                "args": ["monday", 2],
            },
        ]

        for sched in schedules:
            crontab, created = CrontabSchedule.objects.get_or_create(
                minute=sched.get("minute", "0"),
                hour=sched["hour"],
                day_of_week=sched["day_of_week"],
                day_of_month="*",
                month_of_year="*",
                timezone=sched["timezone"],
            )
            if created:
                self.stdout.write(f"Created crontab: {sched['name']}")

            PeriodicTask.objects.update_or_create(
                name=sched["name"],
                defaults={
                    "crontab": crontab,
                    "task": "admin_app.tasks.send_timesheet_reminder",
                    "args": json.dumps(sched["args"]),
                    "enabled": True,
                },
            )
            self.stdout.write(self.style.SUCCESS(f"Task created/updated: {sched['name']}"))

        self.stdout.write(self.style.SUCCESS("✅ All timesheet reminder tasks created successfully."))
