# apps/cart/tests.py
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from apps.products.models import Product, ProductImage, ProductVariant
from .models import Cart, CartItem


class CartMergeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(name="Test Product", price="19.99")
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size="M",
            color="Black",
            sku="TEST-BLK-M",
            price="19.99",
            stock=10,
        )
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="pass12345",
        )

    def test_merge_session_cart_on_login(self):
        # Create a session by making a request.
        self.client.get("/")
        session_key = self.client.session.session_key

        session_cart = Cart.objects.create(session_key=session_key, is_active=True)
        CartItem.objects.create(cart=session_cart, variant=self.variant, quantity=2)
        session = self.client.session
        session["cart_id"] = session_cart.id
        session.save()

        logged_in = self.client.login(email="user@example.com", password="pass12345")
        self.assertTrue(logged_in)

        user_cart = Cart.objects.get(user=self.user, is_active=True)
        item = CartItem.objects.get(cart=user_cart, variant=self.variant)
        self.assertEqual(item.quantity, 2)

        session_cart.refresh_from_db()
        self.assertFalse(session_cart.is_active)


class CartItemTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Test Product", price="10.00")
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size="L",
            color="Blue",
            sku="TEST-BLU-L",
            price="10.00",
            stock=10,
        )
        self.cart = Cart.objects.create(session_key="testsession", is_active=True)

    def test_cart_subtotal(self):
        CartItem.objects.create(cart=self.cart, variant=self.variant, quantity=3)
        self.assertEqual(str(self.cart.subtotal), "30.00")


class CartViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(name="Test Product", price="9.99")
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size="42",
            color="White",
            sku="TEST-WHT-42",
            price="9.99",
            stock=10,
        )

    def test_add_and_remove_item(self):
        response = self.client.post(f"/cart/add/{self.variant.public_id}/", {"quantity": 2})
        self.assertEqual(response.status_code, 302)

        cart = Cart.objects.get(is_active=True)
        item = CartItem.objects.get(cart=cart, variant=self.variant)
        self.assertEqual(item.quantity, 2)

        response = self.client.post(f"/cart/remove/{self.variant.public_id}/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CartItem.objects.filter(cart=cart, variant=self.variant).exists())

    def test_add_to_cart_redirects_to_next(self):
        response = self.client.post(
            f"/cart/add/{self.variant.public_id}/",
            {"quantity": 1, "next": "/shop/"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/shop/")

    def test_add_by_variant_endpoint_works(self):
        response = self.client.post(
            "/cart/add/",
            {"variant_public_id": str(self.variant.public_id), "quantity": 1},
        )
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(is_active=True)
        item = CartItem.objects.get(cart=cart, variant=self.variant)
        self.assertEqual(item.quantity, 1)

    def test_add_blocks_when_quantity_exceeds_stock(self):
        self.variant.stock = 1
        self.variant.save(update_fields=["stock", "updated"])
        response = self.client.post(f"/cart/add/{self.variant.public_id}/", {"quantity": 2})
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(is_active=True)
        self.assertFalse(CartItem.objects.filter(cart=cart, variant=self.variant).exists())

    def test_cart_detail_shows_item_thumbnail(self):
        image = ProductImage.objects.create(
            product=self.product,
            is_primary=True,
            image_thumb=SimpleUploadedFile("cart-thumb.webp", b"fake-webp-bytes", content_type="image/webp"),
        )
        self.client.post(f"/cart/add/{self.variant.public_id}/", {"quantity": 1})

        response = self.client.get("/cart/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, image.image_thumb.url)
