from django import template
register = template.Library()

FIELD_LABELS = {
    "display_name": "الفئة", "parent": "القسم الرئيسي", "is_active": "نشط",
    "sort_order": "الترتيب", "name": "الاسم", "starts_at": "البداية",
    "ends_at": "النهاية", "slug": "الرابط المختصر", "hex_code": "اللون",
    "code": "الكود", "discount_type": "نوع الخصم", "value": "القيمة", "uses": "الاستخدامات",
    "product": "المنتج", "color": "اللون", "size": "المقاس", "sku": "كود المخزون",
    "stock_quantity": "الكمية", "alt_text": "وصف الصورة", "is_primary": "رئيسية",
    "email": "البريد الإلكتروني", "created_at": "تاريخ الإضافة", "phone": "الهاتف",
    "subject": "الموضوع", "status": "الحالة", "customer_name": "العميل",
    "customer_phone": "الهاتف", "customer_email": "البريد الإلكتروني",
    "order_count": "عدد الطلبات", "spend": "إجمالي المشتريات",
}


@register.filter
def field_label(name):
    return FIELD_LABELS.get(name, str(name).replace("_", " "))


@register.filter
def field_value(obj, name):
    if isinstance(obj, dict):
        value = obj.get(name, "—")
        return value if value not in (None, "") else "—"
    display = getattr(obj, f"get_{name}_display", None)
    if callable(display):
        return display()
    value = getattr(obj, name, "—")
    if callable(value): value = value()
    if isinstance(value, bool): return "نعم" if value else "لا"
    return value if value not in (None, "") else "—"
