from django.db.models import Prefetch
from django.shortcuts import render
from django.http import JsonResponse
from apps.catalog.models import Category, Collection, Product, ProductImage
from apps.marketing.models import NewsletterSubscriber
from django.contrib import messages
from django.shortcuts import redirect

def home(request):
    products = Product.objects.available().prefetch_related("images", "variants__color", "variants__size")
    context = {
        "featured_products": products.filter(featured=True)[:4],
        "best_sellers": products.filter(bestseller=True)[:6],
        "categories": Category.objects.filter(is_active=True)[:6],
        "featured_collection": Collection.objects.filter(is_active=True).first(),
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
    return render(request, "store/search.html", {"query": q, "products": products})


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
            "image": product.primary_image.image.url if product.primary_image else "",
        }
        for product in products
    ]})

def newsletter(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        if email and "@" in email:
            NewsletterSubscriber.objects.update_or_create(email=email, defaults={"is_active": True})
            messages.success(request, "أصبحت قريبًا من الإصدار القادم.")
        else: messages.error(request, "أدخل بريدًا إلكترونيًا صحيحًا.")
    return redirect(request.POST.get("next") or "core:home")

def info_page(request, page):
    pages = {
        "about": ("من نحن", "MEMO علامة أزياء معاصرة من القاهرة. نصمم قطعًا يومية بهوية واضحة، بخامات مختارة وقَصّات تُحترم فيها الحركة."),
        "shipping": ("الشحن", "نجهّز الطلبات خلال يومي عمل، ويصل الشحن القياسي عادة خلال 2–5 أيام عمل داخل مصر."),
        "returns": ("الاستبدال والاسترجاع", "يمكن طلب الاسترجاع خلال 14 يومًا من الاستلام للقطع غير المستخدمة وبحالتها الأصلية."),
        "privacy": ("الخصوصية", "نستخدم بياناتك لتنفيذ الطلب وخدمتك فقط، ولا نبيع بيانات العملاء أو نشاركها لأغراض إعلانية خارجية."),
        "terms": ("الشروط", "تخضع الطلبات لتأكيد المخزون وبيانات التوصيل. الأسعار المعروضة بالجنيه المصري وتشمل الضرائب المطبقة."),
        "sizes": ("دليل المقاسات", "اختر مقاسك المعتاد لقَصّة MEMO الواسعة. قياسات كل قطعة تُراجع قبل الإطلاق، ويمكنك التواصل معنا قبل الطلب."),
        "contact": ("تواصل معنا", "للدعم بخصوص الطلبات، اكتب إلى support@memo.example مع رقم الطلب وسنرد خلال يوم عمل."),
    }
    title, content = pages.get(page, pages["about"])
    return render(request, "store/info-page.html", {"title": title, "page_content": content})

def error_403(request, exception=None): return render(request, "errors/403.html", status=403)
def error_404(request, exception=None): return render(request, "errors/404.html", status=404)
def error_500(request): return render(request, "errors/500.html", status=500)
