from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0017_alter_category_cover_image_and_more"),
        ("csm", "0006_footercontent_links"),
    ]

    operations = [
        migrations.AddField(
            model_name="homeherocontent",
            name="primary_cta_category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="products.category",
                verbose_name="Kategória pre prvé tlačidlo",
            ),
        ),
        migrations.AddField(
            model_name="homeherocontent",
            name="secondary_cta_category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="products.category",
                verbose_name="Kategória pre druhé tlačidlo",
            ),
        ),
        migrations.AddField(
            model_name="homeherocontent",
            name="tertiary_cta_category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="products.category",
                verbose_name="Kategória pre tretie tlačidlo",
            ),
        ),
    ]
