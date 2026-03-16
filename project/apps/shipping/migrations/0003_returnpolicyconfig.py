from django.db import migrations, models
import django.db.models


class Migration(migrations.Migration):
    dependencies = [
        ("shipping", "0002_shippingproviderconfig_delivery_eta_label"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReturnPolicyConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="Default policy", max_length=120)),
                ("is_active", models.BooleanField(default=True)),
                ("return_window_days", models.PositiveIntegerField(default=30)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-is_active", "name", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="returnpolicyconfig",
            constraint=models.UniqueConstraint(
                condition=django.db.models.Q(("is_active", True)),
                fields=("is_active",),
                name="uniq_active_return_policy_config",
            ),
        ),
    ]
