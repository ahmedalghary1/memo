from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, register_converter
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from django.conf.urls.i18n import set_language
from apps.core.sitemaps import StaticSitemap, ProductSitemap, CategorySitemap, CollectionSitemap
from apps.core.converters import UnicodeSlugConverter

register_converter(UnicodeSlugConverter, "uslug")

urlpatterns = [
    path("i18n/setlang/", set_language, name="set_language"),
    path("django-admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("shop/", include("apps.catalog.urls")),
    path("cart/", include("apps.cart.urls")),
    path("wishlist/", include("apps.wishlist.urls")),
    path("checkout/", include("apps.checkout.urls")),
    path("orders/", include("apps.orders.urls")),
    path("api/whatsapp/", include("apps.orders.whatsapp.urls")),
    path("account/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("sitemap.xml", sitemap, {"sitemaps": {"static": StaticSitemap, "products": ProductSitemap, "categories": CategorySitemap, "collections": CollectionSitemap}}, name="sitemap"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
