from django import template
register = template.Library()
@register.filter
def field_value(obj, name):
    if isinstance(obj, dict): return obj.get(name, "—")
    value = getattr(obj, name, "—")
    if callable(value): value = value()
    if isinstance(value, bool): return "نعم" if value else "لا"
    return value if value not in (None, "") else "—"
