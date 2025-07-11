# from datetime import timedelta
#
# def calculate_leave_days(start_date, end_date, holidays, floating_holidays, employee):
#     leave_days = 0
#     floating_holiday_count = 0  # Track how many floating holidays are used
#     current_date = start_date
#
#     while current_date <= end_date:
#         # Skip weekends (Saturday and Sunday)
#         if current_date.weekday() in [5, 6]:  # 5 = Saturday, 6 = Sunday
#             current_date += timedelta(days=1)
#             continue
#         # Skip fixed holidays
#         if current_date in holidays:
#             current_date += timedelta(days=1)
#             continue
#         # Handle floating holidays
#         if current_date in floating_holidays:
#             # Check if the employee has used fewer than 2 floating holidays
#             if floating_holiday_count < 2:
#                 floating_holiday_count += 1  # Count this day as a floating holiday
#             else:
#                 # If more than 2 floating holidays, count this as regular leave
#                 leave_days += 1
#             current_date += timedelta(days=1)
#             continue
#
#         leave_days += 1  # Count regular leave day
#         current_date += timedelta(days=1)
#
#     return leave_days






# main utils file below

#
from datetime import timedelta
from employee_app.models import Holiday, FloatingHoliday


def calculate_leave_duration(start_date, end_date, employee):
    """
    Calculate the leave duration excluding weekends, holidays, and floating holidays.

    Args:
    - start_date: The start date of the leave.
    - end_date: The end date of the leave.
    - employee: The employee for whom the leave request is made.

    Returns:
    - leave_duration: The total leave days excluding weekends, holidays, and floating holidays.
    """
    leave_duration = 0
    current_date = start_date

    # Get the holiday dates from the Holiday model (using 'date' as the field name)
    holidays = Holiday.objects.values_list('date', flat=True)

    # Get the floating holiday dates from the FloatingHoliday model (using 'date' as the field name)
    floating_holidays = FloatingHoliday.objects.values_list('date', flat=True)

    # Iterate through each day between start_date and end_date
    while current_date <= end_date:
        # Check if the current day is a weekend (Saturday or Sunday)
        if current_date.weekday() in [5, 6]:
            # Skip weekends
            current_date += timedelta(days=1)
            continue

        # Check if the current day is a holiday (from the Holiday model)
        if current_date in holidays:
            # Skip holidays
            current_date += timedelta(days=1)
            continue

        # Check if the current day is a floating holiday (from the FloatingHoliday model)
        if current_date in floating_holidays:
            # Skip floating holidays
            current_date += timedelta(days=1)
            continue

        # If it's not a weekend, holiday, or floating holiday, count it as a leave day
        leave_duration += 1
        current_date += timedelta(days=1)

    return leave_duration

from .models import LeaveDetails , FloatingHolidayPolicy, HolidayPolicy
from datetime import date
def get_leave_policy_details(employee, referenced_year=None):

    if referenced_year == None:
        referenced_year=date.today().year
    
    #employee experience
    experience=date.today().year - employee.enc_valid_from.year - ((date.today().month, date.today().day) < (employee.enc_valid_from.month, employee.enc_valid_from.day))

    #floating
    floating_holiday_policy= FloatingHolidayPolicy.objects.filter(country=employee.country,year=referenced_year).first()
    allowed_floating_holiday_policy = floating_holiday_policy.allowed_floating_holidays


    #Casual
    Holiday_policy = HolidayPolicy.objects.filter(country=employee.country,year=referenced_year,min_years_experience__lte=experience).order_by('-min_years_experience').first()
    

    return {
            "allowed_floating_holiday_policy":floating_holiday_policy.allowed_floating_holidays if floating_holiday_policy else None,
            "allowed_holiday_policy":Holiday_policy.ordinary_holidays_count + Holiday_policy.extra_holidays if Holiday_policy else None,
            }