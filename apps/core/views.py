from django.db.models import Prefetch, Q
from django.shortcuts import render
from django.http import JsonResponse
from apps.catalog.models import Category, Collection, Product, ProductImage
from apps.marketing.models import NewsletterSubscriber
from django.contrib import messages
from django.shortcuts import redirect
from django.core.paginator import Paginator
from django.utils import timezone
from .forms import ContactMessageForm
from .models import InfoPageContent

def home(request):
    products = Product.objects.available().prefetch_related("images", "variants__color", "variants__size")
    active_categories = Category.objects.filter(is_active=True)
    home_categories = list(active_categories.filter(parent__isnull=True)[:6])
    if not home_categories:
        home_categories = list(active_categories[:6])
    now = timezone.now()
    featured_collection = (
        Collection.objects.filter(is_active=True)
        .filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        .first()
    )
    context = {
        "featured_products": products.filter(new_arrival=True)[:4],
        "best_sellers": products.filter(bestseller=True)[:6],
        "categories": home_categories,
        "featured_collection": featured_collection,
    }
    return render(request, "store/home.html", context)

def search(request):
    q = request.GET.get("q", "").strip()
    products = Product.objects.available()
    if q:
        from django.db.models import Q
        products = products.filter(Q(name__icontains=q) | Q(base_sku__icontains=q) | Q(category__name__icontains=q) | Q(collections__name__icontains=q)).distinct()
    else:
        products = products.none()
    products = products.prefetch_related("images", "variants__color", "variants__size")
    page_obj = Paginator(products, 12).get_page(request.GET.get("page"))
    return render(request, "store/search.html", {"query": q, "products": page_obj, "page_obj": page_obj})


def search_suggestions(request):
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})
    from django.db.models import Q
    products = Product.objects.available().filter(
        Q(name__icontains=q) | Q(base_sku__icontains=q) | Q(category__name__icontains=q)
    ).distinct().prefetch_related("images")[:6]
    return JsonResponse({"results": [
        {
            "name": product.name,
            "category": product.category.name,
            "price": f"{product.price:.0f}",
            "url": product.get_absolute_url(),
            "image": product.primary_image.optimized_url if product.primary_image else "",
        }
        for product in products
    ]})

def newsletter(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        if email and "@" in email:
            NewsletterSubscriber.objects.update_or_create(email=email, defaults={"is_active": True})
            messages.success(request, "You are on the list for the next release.")
        else: messages.error(request, "Enter a valid email address.")
    return redirect(request.POST.get("next") or "core:home")

def info_page(request, page):
    pages = {
        "about": ("About us", "MEMO is a contemporary fashion brand from Cairo. We design everyday pieces with a clear identity, selected fabrics, and cuts made for movement."),
        "shipping": ("Shipping", "We prepare orders within two business days. Standard delivery within Egypt usually takes 2–5 business days."),
        "returns": ("Exchanges and returns", "You can request a return within 14 days of delivery for unused items in their original condition."),
        "privacy": ("Privacy", "We use your data only to process your order and support you. We do not sell customer data or share it for external advertising."),
        "terms": ("Terms", "Orders are subject to stock and delivery confirmation. Prices are in Egyptian pounds and include applicable taxes."),
        "sizes": ("Size guide", "Choose your usual size for MEMO's relaxed fit. We review measurements for every piece before launch, and you can contact us before ordering."),
        "contact": ("Contact us", "Send your question or order details directly to our customer support team."),
    }
    title, content = pages.get(page, pages["about"])
    edited_page = InfoPageContent.objects.filter(page=page).first()
    if edited_page:
        title, content = edited_page.title, edited_page.intro
    contact_form = None
    if page == "contact":
        contact_form = ContactMessageForm(request.POST or None)
        if request.method == "POST" and contact_form.is_valid():
            contact_form.save()
            messages.success(request, "Your message has reached the MEMO team. We will get back to you soon.")
            return redirect("core:info", page="contact")
    return render(request, "store/info-page.html", {"title": title, "page_content": content, "custom_body": edited_page.body if edited_page else "", "page": page, "contact_form": contact_form})

def error_403(request, exception=None): return render(request, "errors/403.html", status=403)
def error_404(request, exception=None): return render(request, "errors/404.html", status=404)
def error_500(request): return render(request, "errors/500.html", status=500)
