from decimal import Decimal

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from apps.orders.admin import OrderAdmin
from apps.orders.models import Address, Order, OrderItem, OrderStatusEvent
from apps.products.models import Product, ProductVariant

pytestmark = pytest.mark.django_db


def _admin_request(django_user_model):
    request = RequestFactory().get("/admin/orders/order/")
    request.user = django_user_model.objects.create_superuser(email="admin@example.com", password="pass12345")
    return request


def _order(*, status=Order.Status.PENDING, variant=None, quantity=1):
    address = Address.objects.create(
        full_name="John Doe",
        email="buyer@example.com",
        phone="+421000000000",
        country="SK",
        city="Bratislava",
        address_line1="Main 1",
    )
    order = Order.objects.create(
        email="buyer@example.com",
        status=status,
        shipping_address=address,
        subtotal=Decimal("25.00"),
        shipping_cost=Decimal("4.90"),
        total=Decimal("29.90"),
    )
    if variant is not None:
        OrderItem.objects.create(
            order=order,
            variant=variant,
            quantity=quantity,
            product_name=variant.product.name,
            sku=variant.sku,
            size=variant.size,
            color=variant.color,
            unit_price=variant.price,
            line_total=variant.price * quantity,
        )
    return order


def test_order_admin_marks_only_paid_orders_shipped(django_user_model):
    admin_instance = OrderAdmin(Order, AdminSite())
    admin_instance.message_user = lambda *args, **kwargs: None
    request = _admin_request(django_user_model)
    paid_order = _order(status=Order.Status.PAID)
    pending_order = _order(status=Order.Status.PENDING)

    admin_instance.mark_paid_orders_shipped(request, Order.objects.filter(id__in=[paid_order.id, pending_order.id]))

    paid_order.refresh_from_db()
    pending_order.refresh_from_db()
    assert paid_order.status == Order.Status.SHIPPED
    assert pending_order.status == Order.Status.PENDING
    assert OrderStatusEvent.objects.filter(
        order=paid_order,
        status=Order.Status.SHIPPED,
        source="admin.mark_shipped",
    ).exists()


def test_order_admin_cancel_pending_orders_restores_stock(django_user_model):
    product = Product.objects.create(name="Admin Coat")
    variant = ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="ADMIN-COAT-M",
        price=Decimal("25.00"),
        stock=3,
    )
    order = _order(status=Order.Status.PENDING, variant=variant, quantity=2)
    admin_instance = OrderAdmin(Order, AdminSite())
    admin_instance.message_user = lambda *args, **kwargs: None
    request = _admin_request(django_user_model)

    admin_instance.cancel_pending_orders(request, Order.objects.filter(id=order.id))

    order.refresh_from_db()
    variant.refresh_from_db()
    assert order.status == Order.Status.CANCELED
    assert variant.stock == 5
    assert OrderStatusEvent.objects.filter(
        order=order,
        status=Order.Status.CANCELED,
        source="admin.cancel_pending",
    ).exists()
