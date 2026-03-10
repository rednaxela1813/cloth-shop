# project/ital/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from django.contrib.sitemaps.views import sitemap as django_sitemap_view
from apps.seo.sitemaps import StaticViewSitemap, ActiveProductSitemap
from apps.seo.views import robots_txt

from apps.csm.views import home_view  # ✅ добавь импорт

sitemaps = {
    "static": StaticViewSitemap,
    "products": ActiveProductSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),

    # ✅ глобальный alias для reverse("home")
    path("", home_view, name="home"),

    # ✅ подключаем остальные страницы csm (help/returns/...)
    path("", include("apps.csm.urls")),

    path("cart/", include("apps.cart.urls")),
    path("checkout/", include("apps.orders.urls")),
    path("shop/", include("apps.products.urls")),
    path("catalog/", include("apps.catalog.urls")),

    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", django_sitemap_view, {"sitemaps": sitemaps}, name="sitemap"),
]

if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
