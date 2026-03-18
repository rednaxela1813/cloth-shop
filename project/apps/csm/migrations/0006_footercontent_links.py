from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0017_alter_category_cover_image_and_more"),
        ("csm", "0005_footercontent"),
    ]

    operations = [
        migrations.AddField(
            model_name="footercontent",
            name="help_contact_url",
            field=models.CharField(default="/contact/", max_length=255, verbose_name="URL odkazu Kontakt"),
        ),
        migrations.AddField(
            model_name="footercontent",
            name="help_customer_care_url",
            field=models.CharField(default="/help/", max_length=255, verbose_name="URL odkazu Customer care"),
        ),
        migrations.AddField(
            model_name="footercontent",
            name="help_returns_url",
            field=models.CharField(default="/returns/", max_length=255, verbose_name="URL odkazu Returns"),
        ),
        migrations.AddField(
            model_name="footercontent",
            name="shop_kids_category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="products.category",
                verbose_name="Kategória pre odkaz Kids",
            ),
        ),
        migrations.AddField(
            model_name="footercontent",
            name="shop_men_category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="products.category",
                verbose_name="Kategória pre odkaz Men",
            ),
        ),
        migrations.AddField(
            model_name="footercontent",
            name="shop_sale_category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="products.category",
                verbose_name="Kategória pre odkaz Sale",
            ),
        ),
        migrations.AddField(
            model_name="footercontent",
            name="shop_women_category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="products.category",
                verbose_name="Kategória pre odkaz Women",
            ),
        ),
    ]
