import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from apps.products.admin import CategoryAdmin, CategoryAdminForm, CategoryChildInline
from apps.products.models import Category

pytestmark = pytest.mark.django_db


def test_category_admin_form_parent_field_is_clearly_named():
    form = CategoryAdminForm()

    assert form.fields["parent"].label == "Parent category"
    assert form.fields["parent"].help_text == (
        "Leave empty for a top-level category. Select a parent only when creating a subcategory."
    )


def test_category_admin_exposes_subcategory_inline():
    admin_instance = CategoryAdmin(Category, AdminSite())

    assert CategoryChildInline in admin_instance.inlines


def test_subcategory_inline_does_not_expose_slug_field():
    assert CategoryChildInline.fields == ("name", "is_active", "sort_order")


def test_category_admin_allows_delete(django_user_model):
    admin_instance = CategoryAdmin(Category, AdminSite())
    request = RequestFactory().get("/admin/products/category/")
    request.user = django_user_model.objects.create_superuser(email="admin@example.com", password="pass12345")

    assert admin_instance.has_delete_permission(request=request) is True
