from django.core.management.base import BaseCommand
from admin_app.models import Employees, LeaveRequest, LeaveDetails , Holiday, FloatingHoliday , HolidayResetPeriod , StateHoliday
from datetime import date , timedelta
from django.utils.timezone import now


class Command(BaseCommand):

    help="syncing the data in production"

    def handle(self, *args, **options):

        today = now().date()
        # change year based on time . this logic need to be checked for future use 
        fin_year_start = date(2025, 4, 1)
        fin_year_end = date(2026, 3, 31)
        
        employees=Employees.objects.all()

        for employee in employees:

            current_year=date.today().year
            reset_period = HolidayResetPeriod.objects.filter(country=employee.country).first()
            if reset_period:
                start_month = reset_period.start_month
                start_day = reset_period.start_day
                end_month=reset_period.end_month
                end_day=reset_period.end_day

                if date.today().month < start_month:
                    current_year-=1
                    fin_year_start = date(current_year, start_month, start_day)
                    fin_year_end = date(current_year+1, end_month, end_day)
                else:
                    fin_year_start = date(current_year, start_month, start_day)
                    fin_year_end = date(current_year+1, end_month, end_day)

            # fixed holidays includes both country holidays and corresponding state holiday
            holidays = set(
            Holiday.objects.filter(
                country=employee.country,
                date__range=(fin_year_start, fin_year_end)
            ).values_list('date', flat=True)
            )
            state_holiday_dates = set(
            StateHoliday.objects.filter(
                country=employee.country,
                state=employee.state
            ).values_list('date', flat=True)
            )
            #combine both 
            holidays |= state_holiday_dates

            floating_holidays = list(
                FloatingHoliday.objects.filter(
                country=employee.country,
                date__range=(fin_year_start, fin_year_end)
            ).values_list('date', flat=True)
            )

            holidays_set = set(holidays)
            floating_holidays_set = set(floating_holidays)

            # --- PRELOAD all relevant leaves for the financial year (used in *all* stats) ---
            leaves_qs = LeaveRequest.objects.filter(
                employee_master=employee,
                start_date__lte=fin_year_end,
                end_date__gte=fin_year_start
            ).only("leave_type", "status", "start_date", "end_date")

            # Pre-slice all leaves into buckets for fast sum in the summary
            leaves_by_type = {k: [] for k, _ in LeaveRequest.LEAVE_TYPES}
            for leave in leaves_qs:
                leaves_by_type.setdefault(leave.leave_type, []).append(leave)

            # Helper: count overlap days, skipping holidays if required
            def overlapping_leave_days(start_date, end_date, fy_start, fy_end, skip_holidays=None):
                if not start_date or not end_date:
                    return 0
                start = max(start_date, fy_start)
                end = min(end_date, fy_end)
                days = 0
                d = start
                while d <= end:
                    if d.weekday() < 5:  # Monday-Friday are 0-4
                        if not skip_holidays or d not in skip_holidays:
                            days += 1
                    d += timedelta(days=1)
                return days if days > 0 else 0


            for leave_type, description in LeaveRequest.LEAVE_TYPES:

                employee_leaves=LeaveDetails.objects.filter(employee=employee,year=current_year).first()

                # get all leaves of this type (for summary)
                lvs = leaves_by_type.get(leave_type, [])
                # Fetch total allowed leaves efficiently
                leave_type_lower = leave_type.lower()
                used_leaves = sum(
                    overlapping_leave_days(l.start_date, l.end_date, fin_year_start, fin_year_end, holidays_set)
                    for l in lvs if l.status in ['Accepted', 'Approved'] and l.end_date < today
                )
                planned_leaves = sum(
                    overlapping_leave_days(l.start_date, l.end_date, fin_year_start, fin_year_end, holidays_set)
                    for l in lvs if l.status in ['Accepted', 'Approved'] and l.end_date >= today
                )
                pending_leaves = sum(
                    overlapping_leave_days(l.start_date, l.end_date, fin_year_start, fin_year_end, holidays_set)
                    for l in lvs if l.status.lower() == 'pending' and l.end_date >= today
                )

                if leave_type_lower == "floating leave":
                    
                    employee_leaves.floating_holidays_used = used_leaves
                    employee_leaves.planned_float = planned_leaves
                    employee_leaves.pending_float = pending_leaves
                    employee_leaves.save()
                
                elif leave_type_lower == "casual leave":

                    employee_leaves.casual_leaves_used = used_leaves
                    employee_leaves.planned_casual = planned_leaves
                    employee_leaves.pending_casual = pending_leaves
                    employee_leaves.save()




