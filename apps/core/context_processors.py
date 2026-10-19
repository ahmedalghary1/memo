from apps.catalog.models import Category, Product
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

    def get_descendants(cat_id):
        desc = [cat_id]
        for child in children.get(cat_id, []):
            desc.extend(get_descendants(child.pk))
        return desc

    cat_to_top = {}
    for top_cat in nav_categories:
        for did in get_descendants(top_cat.pk):
            cat_to_top[did] = top_cat.pk

    if cat_to_top:
        products = (
            Product.objects.available()
            .filter(category_id__in=list(cat_to_top.keys()))
            .prefetch_related("images")
            .order_by("-featured", "-new_arrival", "-created_at")
        )
        top_cat_products = {top_cat.pk: [] for top_cat in nav_categories}
        for product in products:
            top_id = cat_to_top.get(product.category_id)
            if top_id and len(top_cat_products[top_id]) < 4:
                top_cat_products[top_id].append(product)
        for top_cat in nav_categories:
            top_cat.nav_products = top_cat_products.get(top_cat.pk, [])
    else:
        for top_cat in nav_categories:
            top_cat.nav_products = []

    return {"nav_categories": nav_categories, "cart_count": cart.count, "header_cart": cart, "wishlist_product_ids": wishlist_product_ids, "store_settings": store_settings, "standard_shipping": store_settings.standard_shipping}

