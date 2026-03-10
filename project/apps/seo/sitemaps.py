#project/apps/seo/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.products.models import Product


class StaticViewSitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"

    def items(self):
        return ["home", "products:list",  "robots_txt"]  # поправь если у тебя другое имя главной

    def location(self, item):
        return reverse(item)


class ActiveProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True).order_by("-updated", "-created")

    def location(self, obj: Product):
        return reverse("products:detail", kwargs={"public_id": obj.public_id, "slug": obj.slug})
