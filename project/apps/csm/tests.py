from django.test import TestCase
from django.urls import reverse

from apps.products.models import Category, Product, ProductCategory, ProductImage


class HomeViewCategoryTilesTests(TestCase):
    def test_home_view_exposes_random_women_tile_image_url(self):
        women = Category.objects.create(name="Women", slug="women", is_active=True)
        product = Product.objects.create(name="Dress", is_active=True)
        ProductCategory.objects.create(product=product, category=women, is_primary=True)
        ProductImage.objects.create(product=product, image_url="https://example.com/women-1.webp")

        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["women_tile_image_url"], "https://example.com/women-1.webp")
        self.assertEqual(response.context["men_tile_image_url"], "")
        self.assertEqual(response.context["sale_tile_image_url"], "")

    def test_home_view_exposes_random_men_and_sale_tile_image_url(self):
        men = Category.objects.create(name="Men", slug="men", is_active=True)
        sale = Category.objects.create(name="Sale", slug="sale", is_active=True)

        men_product = Product.objects.create(name="Blazer", is_active=True)
        ProductCategory.objects.create(product=men_product, category=men, is_primary=True)
        ProductImage.objects.create(product=men_product, image_url="https://example.com/men-1.webp")

        sale_product = Product.objects.create(name="Promo coat", is_active=True)
        ProductCategory.objects.create(product=sale_product, category=sale, is_primary=True)
        ProductImage.objects.create(product=sale_product, image_url="https://example.com/sale-1.webp")

        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["men_tile_image_url"], "https://example.com/men-1.webp")
        self.assertEqual(response.context["sale_tile_image_url"], "https://example.com/sale-1.webp")
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
