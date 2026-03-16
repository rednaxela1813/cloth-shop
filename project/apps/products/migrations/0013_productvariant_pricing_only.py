from __future__ import annotations

import uuid

from django.db import migrations


def forwards_create_legacy_variants(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    ProductVariant = apps.get_model("products", "ProductVariant")

    for product in Product.objects.filter(variants__isnull=True).iterator():
        ProductVariant.objects.create(
            public_id=uuid.uuid4(),
            product=product,
            size="UNI",
            color="Default",
            sku=f"LEGACY-{product.id}-{uuid.uuid4().hex[:8]}",
            price=product.price,
            compare_at=product.compare_at,
            stock=0,
            is_active=product.is_active,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0012_repair_productvariant_public_id"),
    ]

    operations = [
        migrations.RunPython(forwards_create_legacy_variants, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="product",
            name="compare_at",
        ),
        migrations.RemoveField(
            model_name="product",
            name="price",
        ),
    ]
