
# main utils file below

#
from datetime import timedelta
from .models import LeaveDetails , FloatingHolidayPolicy, HolidayPolicy,HolidayResetPeriod
from datetime import date
def get_leave_policy_details(employee, referenced_year=None):

    if referenced_year == None:
        referenced_year=date.today().year
    
    #employee experience
    experience=date.today().year - employee.enc_valid_from.year - ((date.today().month, date.today().day) < (employee.enc_valid_from.month, employee.enc_valid_from.day))

    #floating
    floating_holiday_policy= FloatingHolidayPolicy.objects.filter(country=employee.country,year=referenced_year).first()


    #Casual
    Holiday_policy = HolidayPolicy.objects.filter(country=employee.country,year=referenced_year,min_years_experience__lte=experience).order_by('-min_years_experience').first()
    

    return {
            "allowed_floating_holiday_policy":floating_holiday_policy.allowed_floating_holidays if floating_holiday_policy else None,
            "allowed_holiday_policy":Holiday_policy.ordinary_holidays_count + Holiday_policy.extra_holidays if Holiday_policy else None,
            }

from math import ceil 
def update_total_leaves(employee,resgn_date,fy_start,fy_end):
    
    year = fy_start.year
    joining_date = employee.enc_valid_from

    try:
        leave_details_record = LeaveDetails.objects.get(employee=employee,year=year)
    except LeaveDetails.DoesNotExist:
        return 0

    total_leaves = leave_details_record.total_casual_leaves

    if fy_start<=joining_date<=fy_end:

        total_days_worked = (resgn_date - joining_date).days +1
        total_days = (fy_end - joining_date).days + 1 
        prorated_leaves = ceil((total_days_worked*total_leaves)/total_days)

        return prorated_leaves
    
    else:
        total_days_worked = (resgn_date - fy_start).days +1
        total_days = (fy_end - fy_start).days + 1 
        prorated_leaves = ceil((total_days_worked*total_leaves)/total_days)

        return prorated_leaves
