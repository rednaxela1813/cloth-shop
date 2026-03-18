from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
import io
import tempfile
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.csm.models import FooterContent, HomeHeroContent, SiteBranding
from apps.products.models import Category, Product, ProductCategory


class HealthzViewTests(SimpleTestCase):
    def test_healthz_returns_ok(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "ok")


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class SiteBrandingTests(TestCase):
    def _uploaded_logo(self, *, name="logo.png", size=(640, 640), color=(0, 0, 0, 0)):
        file_obj = io.BytesIO()
        image = Image.new("RGBA", size, color)
        image.save(file_obj, format="PNG")
        file_obj.seek(0)
        return SimpleUploadedFile(name, file_obj.read(), content_type="image/png")

    def test_site_branding_generates_header_logo_and_exposes_it_in_home_context(self):
        branding = SiteBranding.objects.create(
            site_name="Ricotti Atelier",
            logo_alt="Ricotti logo",
            logo_original=self._uploaded_logo(),
        )

        response = self.client.get(reverse("pages:home"))

        branding.refresh_from_db()
        self.assertTrue(bool(branding.logo_header))
        self.assertIn(".webp", branding.logo_header.name)
        self.assertEqual(response.context["site_brand_name"], "Ricotti Atelier")
        self.assertEqual(response.context["site_logo_alt"], "Ricotti logo")
        self.assertEqual(response.context["site_logo_url"], branding.logo_header.url)


class HomeViewCategoryTilesTests(TestCase):
    def _set_product_created_days_ago(self, product, *, days_ago):
        Product.objects.filter(pk=product.pk).update(created=timezone.now() - timedelta(days=days_ago))
        product.refresh_from_db()
        return product

    def test_home_view_exposes_women_tile_image_url_from_category_cover(self):
        Category.objects.create(
            name="Women",
            slug="women",
            is_active=True,
            cover_image_url="https://example.com/women-cover.webp",
        )

        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["women_tile_image_url"], "https://example.com/women-cover.webp")
        self.assertEqual(response.context["men_tile_image_url"], "")
        self.assertEqual(response.context["sale_tile_image_url"], "")

    def test_home_view_exposes_men_and_sale_tile_image_url_from_category_cover(self):
        Category.objects.create(
            name="Men",
            slug="men",
            is_active=True,
            cover_image_url="https://example.com/men-cover.webp",
        )
        Category.objects.create(
            name="Sale",
            slug="sale",
            is_active=True,
            cover_image_url="https://example.com/sale-cover.webp",
        )

        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["men_tile_image_url"], "https://example.com/men-cover.webp")
        self.assertEqual(response.context["sale_tile_image_url"], "https://example.com/sale-cover.webp")
        self.assertEqual(response.context["women_tile_image_url"], "")

    def test_home_view_exposes_empty_women_tile_image_url_without_images(self):
        Category.objects.create(name="Women", slug="women", is_active=True)

        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["women_tile_image_url"], "")
        self.assertEqual(response.context["men_tile_image_url"], "")
        self.assertEqual(response.context["sale_tile_image_url"], "")

    def test_home_view_filters_trending_by_selected_category(self):
        women = Category.objects.create(name="Women", slug="women", is_active=True)
        men = Category.objects.create(name="Men", slug="men", is_active=True)

        women_product = Product.objects.create(name="Women Dress", is_active=True, is_trending=True)
        men_product = Product.objects.create(name="Men Blazer", is_active=True, is_trending=True)

        ProductCategory.objects.create(product=women_product, category=women, is_primary=True)
        ProductCategory.objects.create(product=men_product, category=men, is_primary=True)

        response = self.client.get(reverse("pages:home"), {"category": "women"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["trending_products"]), [women_product])
        self.assertEqual(response.context["selected_category_slug"], "women")
        self.assertEqual(response.context["selected_subcategory_slug"], "")

    def test_home_view_filters_trending_by_selected_subcategory(self):
        women = Category.objects.create(name="Women", slug="women", is_active=True)
        dresses = Category.objects.create(name="Dresses", slug="dresses", is_active=True, parent=women)
        shoes = Category.objects.create(name="Shoes", slug="shoes", is_active=True, parent=women)

        dress_product = Product.objects.create(name="Silk Dress", is_active=True, is_trending=True)
        shoes_product = Product.objects.create(name="Leather Shoes", is_active=True, is_trending=True)

        ProductCategory.objects.create(product=dress_product, category=dresses, is_primary=True)
        ProductCategory.objects.create(product=shoes_product, category=shoes, is_primary=True)

        response = self.client.get(
            reverse("pages:home"),
            {"category": "women", "subcategory": "dresses"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["trending_products"]), [dress_product])
        self.assertEqual(response.context["selected_category_slug"], "women")
        self.assertEqual(response.context["selected_subcategory_slug"], "dresses")
        self.assertEqual(list(response.context["subcategories"]), [dresses, shoes])

    def test_home_view_trending_cards_link_to_product_detail(self):
        women = Category.objects.create(name="Women", slug="women", is_active=True)
        product = Product.objects.create(name="Silk Dress", is_active=True, is_trending=True)
        ProductCategory.objects.create(product=product, category=women, is_primary=True)

        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("products:detail", kwargs={"public_id": product.public_id, "slug": product.slug}),
        )

    def test_home_view_shows_new_arrivals_button_when_recent_products_exist(self):
        recent_product = Product.objects.create(name="Fresh Coat", is_active=True)
        self._set_product_created_days_ago(recent_product, days_ago=3)

        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_new_arrivals"])
        self.assertContains(response, reverse("products:list") + "?new=1")
        self.assertContains(response, "Novinky")

    def test_home_view_hides_new_arrivals_button_without_recent_products(self):
        stale_product = Product.objects.create(name="Archive Coat", is_active=True)
        self._set_product_created_days_ago(stale_product, days_ago=20)

        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_new_arrivals"])
        self.assertNotContains(response, reverse("products:list") + "?new=1")

    def test_home_view_uses_hero_content_from_admin(self):
        women = Category.objects.create(name="Women", slug="women", is_active=True)
        men = Category.objects.create(name="Men", slug="men", is_active=True)
        sale = Category.objects.create(name="Sale", slug="sale", is_active=True)
        editorial = Category.objects.create(name="Editorial", slug="editorial", is_active=True, parent=women)

        HomeHeroContent.objects.create(
            eyebrow="Kurátorovaný výber",
            title="Nový hero nadpis",
            description="Nový hero popis.",
            primary_cta_label="Pre ženy",
            primary_cta_category=editorial,
            secondary_cta_label="Pre mužov",
            secondary_cta_category=men,
            tertiary_cta_label="Pozrieť zľavy",
            tertiary_cta_category=sale,
            delivery_title="Rýchle doručenie",
            delivery_text="Doručíme v priebehu pár dní.",
            authenticity_title="Overený pôvod",
            authenticity_text="Každý kus prechádza kontrolou.",
        )

        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kurátorovaný výber")
        self.assertContains(response, "Nový hero nadpis")
        self.assertContains(response, "Nový hero popis.")
        self.assertContains(response, "Pre ženy")
        self.assertContains(response, "Pre mužov")
        self.assertContains(response, "Pozrieť zľavy")
        self.assertContains(response, "Rýchle doručenie")
        self.assertContains(response, "Doručíme v priebehu pár dní.")
        self.assertContains(response, "Overený pôvod")
        self.assertContains(response, "Každý kus prechádza kontrolou.")
        self.assertContains(response, 'href="/catalog/editorial/"', html=False)
        self.assertContains(response, 'href="/catalog/men/"', html=False)
        self.assertContains(response, 'href="/catalog/sale/"', html=False)

    def test_home_view_uses_footer_content_from_admin(self):
        women = Category.objects.create(name="Women", slug="women", is_active=True)
        men = Category.objects.create(name="Men", slug="men", is_active=True)
        kids = Category.objects.create(name="Kids", slug="kids", is_active=True)
        sale = Category.objects.create(name="Sale", slug="sale", is_active=True)
        custom_women = Category.objects.create(name="Evening", slug="evening", is_active=True, parent=women)

        FooterContent.objects.create(
            description="Nový footer popis.",
            shop_title="Nakupovať",
            shop_women_label="Ženy",
            shop_women_category=custom_women,
            shop_men_label="Muži",
            shop_men_category=men,
            shop_kids_label="Deti",
            shop_kids_category=kids,
            shop_sale_label="Výpredaj",
            shop_sale_category=sale,
            help_title="Pomoc",
            help_customer_care_label="Zákaznícka podpora",
            help_customer_care_url="/pomoc/",
            help_returns_label="Vrátenie",
            help_returns_url="/vratenie/",
            help_contact_label="Kontaktujte nás",
            help_contact_url="/napiste-nam/",
            legal_title="Právne informácie",
            copyright_text="Ricotti s.r.o. Všetky práva vyhradené.",
            badge_primary="Pripravené pre SK/EU",
            badge_secondary="Bezpečný nákup",
        )

        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nový footer popis.")
        self.assertContains(response, "Nakupovať")
        self.assertContains(response, "Ženy")
        self.assertContains(response, "Muži")
        self.assertContains(response, "Deti")
        self.assertContains(response, "Výpredaj")
        self.assertContains(response, "Pomoc")
        self.assertContains(response, "Zákaznícka podpora")
        self.assertContains(response, "Vrátenie")
        self.assertContains(response, "Kontaktujte nás")
        self.assertContains(response, "Právne informácie")
        self.assertContains(response, "Ricotti s.r.o. Všetky práva vyhradené.")
        self.assertContains(response, "Pripravené pre SK/EU")
        self.assertContains(response, "Bezpečný nákup")
        self.assertContains(response, 'href="/catalog/evening/"', html=False)
        self.assertContains(response, 'href="/catalog/men/"', html=False)
        self.assertContains(response, 'href="/catalog/kids/"', html=False)
        self.assertContains(response, 'href="/catalog/sale/"', html=False)
        self.assertContains(response, 'href="/pomoc/"', html=False)
        self.assertContains(response, 'href="/vratenie/"', html=False)
        self.assertContains(response, 'href="/napiste-nam/"', html=False)
