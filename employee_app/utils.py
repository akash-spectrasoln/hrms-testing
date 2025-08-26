
# main utils file below

#
from datetime import timedelta
from .models import LeaveDetails , FloatingHolidayPolicy, HolidayPolicy
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