from apps.catalog.models import Category
from apps.cart.services import Cart
from apps.core.models import StoreSettings

def store_context(request):
    cart = Cart(request)
    wishlist_product_ids = set()
    if request.user.is_authenticated:
        wishlist_product_ids = set(request.user.wishlist_items.values_list("product_id", flat=True))
    store_settings = StoreSettings.load()
    categories = list(Category.objects.filter(is_active=True).order_by("sort_order", "name"))
    children = {}
    for category in categories:
        children.setdefault(category.parent_id, []).append(category)
    for category in categories:
        category.nav_children = children.get(category.pk, [])
    nav_categories = children.get(None, [])
    return {"nav_categories": nav_categories, "cart_count": cart.count, "header_cart": cart, "wishlist_product_ids": wishlist_product_ids, "store_settings": store_settings, "standard_shipping": store_settings.standard_shipping}
