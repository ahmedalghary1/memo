from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.catalog.models import Category, Product

class StaticSitemap(Sitemap):
    priority = .7
    def items(self): return ["core:home", "catalog:list"]
    def location(self, item): return reverse(item)
class ProductSitemap(Sitemap):
    changefreq = "weekly"; priority = .8
    def items(self): return Product.objects.available()
    def lastmod(self, obj): return obj.updated_at
class CategorySitemap(Sitemap):
    changefreq = "weekly"
    def items(self): return Category.objects.filter(is_active=True)
