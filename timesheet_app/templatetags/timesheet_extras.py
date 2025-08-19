from django import template

register = template.Library()

@register.filter
def decimal_hours_to_time(decimal_hours):
    """
    Converts decimal hours (e.g., 8.25) into HH:MM format (e.g., 8:15)
    """
    try:
        total_minutes = int(decimal_hours * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}:{minutes:02d}"
    except:
        return decimal_hours
