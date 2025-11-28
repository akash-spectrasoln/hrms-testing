# timesheetcron.py
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = "Set up weekly timesheet reminder tasks for India & US employees (UTC schedule)."

    def handle(self, *args, **options):
        # UTC times corresponding to local reminder times:
        # India 10 AM IST → 4:30 AM UTC
        # US 10 AM ET   → 14:00 UTC (adjust if DST)
        # India 5 PM IST → 11:30 AM UTC
        # US 5 PM ET   → 21:00 UTC (adjust if DST)
        schedules = [
            # Monday 10 AM reminders (previous week)
            {
                "name": "Timesheet Reminder Monday 10AM India",
                "hour": "04",
                "minute": "30",
                "day_of_week": "1",  # Monday
                "args": ["monday_morning", 1],  # region_id=1 (India)
            },
            {
                "name": "Timesheet Reminder Monday 10AM US",
                "hour": "14",
                "minute": "00",
                "day_of_week": "1",  # Monday
                "args": ["monday_morning", 2],  # region_id=2 (US)
            },
            # Monday 5 PM reminders (previous week)
            {
                "name": "Timesheet Reminder Monday 5PM India",
                "hour": "11",
                "minute": "30",
                "day_of_week": "1",  # Monday
                "args": ["monday_evening", 1],
            },
            {
                "name": "Timesheet Reminder Monday 5PM US",
                "hour": "21",
                "minute": "00",
                "day_of_week": "1",  # Monday
                "args": ["monday_evening", 2],
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
