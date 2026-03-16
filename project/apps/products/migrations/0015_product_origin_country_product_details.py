from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0014_product_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="details",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="product",
            name="origin_country",
            field=models.CharField(blank=True, default="", max_length=120),
            preserve_default=False,
        ),
    ]
