from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from .models import Category, Color, Collection, Product, ProductVariant, Size

def product_list(request, slug=None):
    products = Product.objects.available().prefetch_related("images", "variants__color", "variants__size")
    category = None
    if slug:
        category = get_object_or_404(Category, slug=slug, is_active=True)
        category_ids = Category.objects.filter(
            Q(pk=category.pk) | Q(parent=category) | Q(parent__parent=category),
            is_active=True,
        ).values_list("pk", flat=True)
        products = products.filter(category_id__in=category_ids)
    size = request.GET.getlist("size")
    color = request.GET.getlist("color")
    if size: products = products.filter(variants__size__slug__in=size)
    if color: products = products.filter(variants__color__slug__in=color)
    if request.GET.get("available"): products = products.filter(variants__stock_quantity__gt=0)
    try:
        if request.GET.get("price_min"): products = products.filter(price__gte=request.GET["price_min"])
        if request.GET.get("price_max"): products = products.filter(price__lte=request.GET["price_max"])
    except (ValueError, TypeError):
        pass
    order = {"price_asc": "price", "price_desc": "-price", "new": "-created_at", "discount": "compare_at_price"}.get(request.GET.get("sort"), "-created_at")
    products = products.distinct().order_by(order)
    page = Paginator(products, 12).get_page(request.GET.get("page"))
    categories = list(Category.objects.filter(is_active=True).select_related("parent", "parent__parent"))
    children = {}
    for item in categories: children.setdefault(item.parent_id, []).append(item)
    for branch in children.values(): branch.sort(key=lambda item: (item.sort_order, item.name))
    all_categories = []
    def append_branch(parent_id=None):
        for item in children.get(parent_id, []):
            all_categories.append(item)
            append_branch(item.pk)
    append_branch()
    direct_counts = dict(Product.objects.filter(status="active", category__in=categories).values_list("category_id").annotate(total=Count("id")))
    def subtree_count(item):
        return direct_counts.get(item.pk, 0) + sum(subtree_count(child) for child in children.get(item.pk, []))
    for item in all_categories: item.active_product_count = subtree_count(item)
    category_children = children.get(category.pk, []) if category else children.get(None, [])
    return render(request, "store/collection.html", {"page_obj": page, "category": category, "category_children": category_children, "sizes": Size.objects.all(), "colors": Color.objects.all(), "all_categories": all_categories, "selected_sizes": size, "selected_colors": color, "selected_size_objects": Size.objects.filter(slug__in=size), "selected_color_objects": Color.objects.filter(slug__in=color), "active_filter_count": len(size)+len(color)+bool(request.GET.get("available"))+bool(request.GET.get("price_min"))+bool(request.GET.get("price_max"))})

def product_detail(request, slug):
    product = get_object_or_404(Product.objects.available().prefetch_related("images", "variants__color", "variants__size"), slug=slug)
    variants = list(product.variants.filter(is_active=True).select_related("color", "size"))
    related = Product.objects.available().filter(category=product.category).exclude(pk=product.pk).prefetch_related("images", "variants__color", "variants__size")[:4]
    return render(request, "store/product-detail.html", {"product": product, "variants": variants, "related": related})
