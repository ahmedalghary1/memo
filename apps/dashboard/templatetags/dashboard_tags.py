from django import template
from django.urls import NoReverseMatch, reverse
register = template.Library()
@register.filter
def field_value(obj, name):
    if isinstance(obj, dict): return obj.get(name, "—")
    value = getattr(obj, name, "—")
    if callable(value): value = value()
    if isinstance(value, bool): return "نعم" if value else "لا"
    return value if value not in (None, "") else "—"

@register.simple_tag
def admin_change_url(obj):
    if isinstance(obj, dict) or not getattr(obj, "pk", None): return ""
    try:
        return reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk])
    except NoReverseMatch:
        return ""
