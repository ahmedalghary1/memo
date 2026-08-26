from apps.catalog.models import Category
from apps.cart.services import Cart

def store_context(request):
    cart = Cart(request)
    return {"nav_categories": Category.objects.filter(is_active=True, parent__isnull=True)[:6], "cart_count": cart.count, "header_cart": cart}
