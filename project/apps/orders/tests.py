# apps/orders/tests.py
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.cart.models import Cart, CartItem
from apps.products.models import Product, ProductVariant
from .models import Address, Order, OrderItem, OrderStatusEvent, Payment, PaymentStatusEvent
from .services import create_order_from_cart


class OrderModelsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="buyer@example.com",
            password="pass12345",
        )
        self.product = Product.objects.create(name="Test Product", price="25.00")
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size="M",
            color="Black",
            sku="ORDER-BLK-M",
            price="25.00",
            stock=10,
        )
        self.address = Address.objects.create(
            user=self.user,
            full_name="John Doe",
            email="buyer@example.com",
            phone="+421000000000",
            country="SK",
            city="Bratislava",
            address_line1="Main 1",
        )

    def test_create_order_with_item(self):
        order = Order.objects.create(
            user=self.user,
            email="buyer@example.com",
            shipping_address=self.address,
            subtotal=Decimal("25.00"),
            shipping_cost=Decimal("5.00"),
            total=Decimal("30.00"),
        )
        item = OrderItem.objects.create(
            order=order,
            variant=self.variant,
            quantity=1,
            product_name=self.product.name,
            sku=self.variant.sku,
            size=self.variant.size,
            color=self.variant.color,
            unit_price=Decimal("25.00"),
            line_total=Decimal("25.00"),
        )

        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(item.subtotal, Decimal("25.00"))
        self.assertEqual(order.status_events.count(), 1)
        self.assertEqual(order.status_events.first().status, Order.Status.PENDING)

    def test_create_payment(self):
        order = Order.objects.create(
            user=self.user,
            email="buyer@example.com",
            shipping_address=self.address,
            subtotal=Decimal("25.00"),
            shipping_cost=Decimal("0.00"),
            total=Decimal("25.00"),
        )
        payment = Payment.objects.create(
            order=order,
            amount=Decimal("25.00"),
            currency="EUR",
        )
        self.assertEqual(payment.provider, Payment.Provider.STRIPE)
        self.assertEqual(payment.status, Payment.Status.CREATED)
        self.assertEqual(payment.status_events.count(), 1)
        self.assertEqual(payment.status_events.first().status, Payment.Status.CREATED)

    def test_order_status_change_creates_history_event(self):
        order = Order.objects.create(
            user=self.user,
            email="buyer@example.com",
            shipping_address=self.address,
            subtotal=Decimal("25.00"),
            shipping_cost=Decimal("0.00"),
            total=Decimal("25.00"),
        )

        order._status_event_source = "test.manual"
        order.status = Order.Status.PAID
        order.save(update_fields=["status", "updated"])

        events = list(OrderStatusEvent.objects.filter(order=order).order_by("created", "id"))
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].status, Order.Status.PENDING)
        self.assertEqual(events[0].source, "system")
        self.assertEqual(events[1].status, Order.Status.PAID)
        self.assertEqual(events[1].source, "test.manual")

    def test_payment_status_change_creates_history_event(self):
        order = Order.objects.create(
            user=self.user,
            email="buyer@example.com",
            shipping_address=self.address,
            subtotal=Decimal("25.00"),
            shipping_cost=Decimal("0.00"),
            total=Decimal("25.00"),
        )
        payment = Payment.objects.create(
            order=order,
            amount=Decimal("25.00"),
            currency="EUR",
        )

        payment._status_event_source = "test.manual"
        payment.status = Payment.Status.PENDING
        payment.save(update_fields=["status", "updated"])

        events = list(PaymentStatusEvent.objects.filter(payment=payment).order_by("created", "id"))
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].status, Payment.Status.CREATED)
        self.assertEqual(events[0].source, "system")
        self.assertEqual(events[1].status, Payment.Status.PENDING)
        self.assertEqual(events[1].source, "test.manual")

    def test_create_order_from_cart_decrements_stock(self):
        cart = Cart.objects.create(user=self.user, is_active=True)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)
        data = {
            "full_name": "John Doe",
            "email": "buyer@example.com",
            "phone": "",
            "country": "SK",
            "shipping_method": Order.ShippingMethod.DPD_HOME,
            "region": "",
            "city": "Bratislava",
            "postal_code": "",
            "address_line1": "Main 1",
            "address_line2": "",
        }

        class DummyRequest:
            pass

        request = DummyRequest()
        request.user = self.user

        order = create_order_from_cart(request, cart, data)

        self.variant.refresh_from_db()
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(self.variant.stock, 8)
        self.assertEqual(order.shipping_method, Order.ShippingMethod.DPD_HOME)
        self.assertEqual(order.shipping_cost, Decimal("4.90"))
        self.assertEqual(order.total, Decimal("54.90"))

    def test_create_order_from_cart_raises_on_insufficient_stock(self):
        self.variant.stock = 1
        self.variant.save(update_fields=["stock", "updated"])
        cart = Cart.objects.create(user=self.user, is_active=True)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)
        data = {
            "full_name": "John Doe",
            "email": "buyer@example.com",
            "phone": "",
            "country": "SK",
            "shipping_method": Order.ShippingMethod.DPD_HOME,
            "region": "",
            "city": "Bratislava",
            "postal_code": "",
            "address_line1": "Main 1",
            "address_line2": "",
        }

        class DummyRequest:
            pass

        request = DummyRequest()
        request.user = self.user

        with self.assertRaises(ValueError):
            create_order_from_cart(request, cart, data)
