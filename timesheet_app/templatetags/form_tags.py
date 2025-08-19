from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Adds a CSS class to a form field widget.
    Safe version: only applies to BoundField objects.
    """
    try:
        return field.as_widget(attrs={"class": css_class})
    except AttributeError:
        # Likely the field is already a string (rendered HTML), return it as is
        return field

