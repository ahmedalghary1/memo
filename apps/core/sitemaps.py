from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from apps.catalog.models import Category, Collection, Product

class StaticSitemap(Sitemap):
    priority = .7
    def items(self): return ["core:home", "catalog:list", "catalog:collections"]
    def location(self, item): return reverse(item)
class ProductSitemap(Sitemap):
    changefreq = "weekly"; priority = .8
    def items(self): return Product.objects.available()
    def lastmod(self, obj): return obj.updated_at
class CategorySitemap(Sitemap):
    changefreq = "weekly"
    def items(self): return Category.objects.filter(is_active=True)

class CollectionSitemap(Sitemap):
    changefreq = "weekly"
    def items(self):
        now = timezone.now()
        return Collection.objects.filter(is_active=True).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now)
        ).filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
    def lastmod(self, obj): return obj.updated_at
