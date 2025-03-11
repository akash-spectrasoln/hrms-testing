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




#
# from datetime import timedelta
# from employee_app.models import Holiday, FloatingHoliday
#
#
# def calculate_leave_duration(start_date, end_date, employee):
#     """
#     Calculate the leave duration excluding weekends, holidays, and floating holidays.
#
#     Args:
#     - start_date: The start date of the leave.
#     - end_date: The end date of the leave.
#     - employee: The employee for whom the leave request is made.
#
#     Returns:
#     - leave_duration: The total leave days excluding weekends, holidays, and floating holidays.
#     """
#     leave_duration = 0
#     floating_holidays_used = 0  # Track the number of floating holidays used
#
#     current_date = start_date
#
#     # Get the holiday dates from the Holiday model (using 'date' as the field name)
#     holidays = Holiday.objects.values_list('date', flat=True)
#
#     # Get the floating holiday dates from the FloatingHoliday model (using 'date' as the field name)
#     floating_holidays = FloatingHoliday.objects.values_list('date', flat=True)
#
#     # Iterate through each day between start_date and end_date
#     while current_date <= end_date:
#         # Check if the current day is a weekend (Saturday or Sunday)
#         if current_date.weekday() in [5, 6]:
#             # Skip weekends
#             current_date += timedelta(days=1)
#             continue
#
#         # Check if the current day is a holiday (from the Holiday model)
#         if current_date in holidays:
#             # Skip holidays
#             current_date += timedelta(days=1)
#             continue
#
#         # Check if the current day is a floating holiday (from the FloatingHoliday model)
#         if current_date in floating_holidays:
#             # Count floating holiday as leave day
#             floating_holidays_used += 1
#             current_date += timedelta(days=1)
#             continue
#
#         # If it's not a weekend, holiday, or floating holiday, count it as a leave day
#         leave_duration += 1
#         current_date += timedelta(days=1)
#
#     return leave_duration, floating_holidays_used

















# from datetime import timedelta
# from employee_app.models import Holiday, FloatingHoliday
#
# def calculate_leave_duration(start_date, end_date, employee):
#     """
#     Calculate the leave duration excluding weekends and holidays.
#     Only the first two floating holidays are skipped; subsequent floating holidays are counted as leave days.
#
#     Args:
#     - start_date: The start date of the leave.
#     - end_date: The end date of the leave.
#     - employee: The employee for whom the leave request is made.
#
#     Returns:
#     - leave_duration: The total leave days excluding weekends and holidays.
#     - floating_holidays_used: The count of floating holidays used in this leave request.
#     """
#     leave_duration = 0
#     floating_holidays_used = 0
#     current_date = start_date
#
#     # Get the holiday dates from the Holiday model
#     holidays = Holiday.objects.values_list('date', flat=True)
#
#     # Get the floating holiday dates from the FloatingHoliday model
#     floating_holidays = FloatingHoliday.objects.values_list('date', flat=True)
#
#     # Iterate through each day between start_date and end_date
#     while current_date <= end_date:
#         # Check if the current day is a weekend (Saturday or Sunday)
#         if current_date.weekday() in [5, 6]:
#             # Skip weekends
#             current_date += timedelta(days=1)
#             continue
#
#         # Check if the current day is a holiday (from the Holiday model)
#         if current_date in holidays:
#             # Skip holidays
#             current_date += timedelta(days=1)
#             continue
#
#         # Check if the current day is a floating holiday
#         if current_date in floating_holidays:
#             # Skip the first two floating holidays; count subsequent ones as leave days
#             if floating_holidays_used < 2:
#                 floating_holidays_used += 1
#                 current_date += timedelta(days=1)
#                 continue
#
#         # If it's not a weekend, holiday, or allowed floating holiday, count it as a leave day
#         leave_duration += 1
#         current_date += timedelta(days=1)
#
#     return leave_duration, floating_holidays_used
