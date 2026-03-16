from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0013_productvariant_pricing_only"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="description",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
    ]
