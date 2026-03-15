from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("shipping", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="shippingproviderconfig",
            name="delivery_eta_label",
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
