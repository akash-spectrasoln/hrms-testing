# timesheetcron.py
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = "Set up weekly timesheet reminder tasks for India & US employees (UTC schedule)."

    def handle(self, *args, **options):
        # UTC times corresponding to local reminder times:
        # India 4 PM IST → 10:30 AM UTC
        # US 4 PM ET   → 20:00 UTC (adjust if DST)
        # India 9 AM IST → 3:30 AM UTC
        # US 9 AM ET   → 13:00 UTC (adjust if DST)
        schedules = [
            # Friday reminders
            {
                "name": "Timesheet Reminder Friday India",
                "hour": "10",
                "minute": "30",
                "day_of_week": "5",  # Friday
                "args": ["friday", 1],  # region_id=1 (India)
            },
            {
                "name": "Timesheet Reminder Friday US",
                "hour": "20",
                "minute": "00",
                "day_of_week": "5",  # Friday
                "args": ["friday", 2],  # region_id=2 (US)
            },
            # Monday reminders
            {
                "name": "Timesheet Reminder Monday India",
                "hour": "03",
                "minute": "30",
                "day_of_week": "1",  # Monday
                "args": ["monday", 1],
            },
            {
                "name": "Timesheet Reminder Monday US",
                "hour": "13",
                "minute": "00",
                "day_of_week": "1",  # Monday
                "args": ["monday", 2],
            },
        ]

        for sched in schedules:
            # Create or reuse the crontab schedule
            crontab, created = CrontabSchedule.objects.get_or_create(
                minute=sched["minute"],
                hour=sched["hour"],
                day_of_week=sched["day_of_week"],
                day_of_month="*",
                month_of_year="*",
                timezone="UTC",
            )
            if created:
                self.stdout.write(f"🆕 Created crontab: {sched['name']}")

            # Create or update the periodic task
            PeriodicTask.objects.update_or_create(
                name=sched["name"],
                defaults={
                    "crontab": crontab,
                    "task": "admin_app.tasks.send_timesheet_reminder",
                    "args": json.dumps(sched["args"]),
                    "enabled": True,
                },
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Task created/updated: {sched['name']}"))

        # Disable any old timesheet tasks no longer listed
        PeriodicTask.objects.filter(
            task="admin_app.tasks.send_timesheet_reminder"
        ).exclude(
            name__in=[s["name"] for s in schedules]
        ).update(enabled=False)

        self.stdout.write(self.style.SUCCESS("🎯 All timesheet reminder tasks set up successfully."))
