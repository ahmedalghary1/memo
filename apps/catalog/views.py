from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from .models import Category, Color, Collection, Product, ProductVariant, Size

def product_list(request, slug=None):
    products = Product.objects.available().prefetch_related("images", "variants__color", "variants__size")
    category = None
    if slug:
        category = get_object_or_404(Category, slug=slug, is_active=True)
        products = products.filter(Q(category=category) | Q(category__parent=category))
    size = request.GET.getlist("size")
    color = request.GET.getlist("color")
    if size: products = products.filter(variants__size__slug__in=size)
    if color: products = products.filter(variants__color__slug__in=color)
    if request.GET.get("available"): products = products.filter(variants__stock_quantity__gt=0)
    order = {"price_asc": "price", "price_desc": "-price", "new": "-created_at", "discount": "compare_at_price"}.get(request.GET.get("sort"), "-created_at")
    products = products.distinct().order_by(order)
    page = Paginator(products, 12).get_page(request.GET.get("page"))
    return render(request, "store/collection.html", {"page_obj": page, "category": category, "sizes": Size.objects.all(), "colors": Color.objects.all()})

def product_detail(request, slug):
    product = get_object_or_404(Product.objects.available().prefetch_related("images", "variants__color", "variants__size"), slug=slug)
    variants = list(product.variants.filter(is_active=True).select_related("color", "size"))
    related = Product.objects.available().filter(category=product.category).exclude(pk=product.pk).prefetch_related("images")[:4]
    return render(request, "store/product-detail.html", {"product": product, "variants": variants, "related": related})
