from datetime import timedelta, date

def calculate_leave_days(start_date, end_date, holidays, floating_holidays):
    total_days = (end_date - start_date).days + 1  # Including both start and end date
    leave_days = total_days

    # Print out initial values for debugging
    print(f"Total days: {total_days}")
    print(f"Holidays: {holidays}")
    print(f"Floating Holidays: {floating_holidays}")

    # Convert holidays and floating holidays to datetime.date if not already
    holidays = [holiday if isinstance(holiday, date) else date(holiday.year, holiday.month, holiday.day) for holiday in holidays]
    floating_holidays = [floating_holiday if isinstance(floating_holiday, date) else date(floating_holiday.year, floating_holiday.month, floating_holiday.day) for floating_holiday in floating_holidays]

    # Loop over the date range and exclude weekends and holidays
    current_date = start_date
    while current_date <= end_date:
        print(f"Checking date: {current_date}")

        # Exclude weekends (Saturday and Sunday)
        if current_date.weekday() in [5, 6]:  # 5 = Saturday, 6 = Sunday
            leave_days -= 1
            print(f"Excluded weekend: {current_date}")

        # Exclude holidays
        elif current_date in holidays:
            leave_days -= 1
            print(f"Excluded holiday: {current_date}")

        # Exclude floating holidays
        elif current_date in floating_holidays:
            leave_days -= 1
            print(f"Excluded floating holiday: {current_date}")

        # Move to the next day
        current_date += timedelta(days=1)

    print(f"Final leave days: {leave_days}")
    return leave_days
