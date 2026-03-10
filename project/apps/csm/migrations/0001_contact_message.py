from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("messenger_type", models.CharField(choices=[("whatsapp", "WhatsApp"), ("telegram", "Telegram"), ("viber", "Viber"), ("signal", "Signal"), ("other", "Iné")], max_length=40)),
                ("messenger_handle", models.CharField(max_length=120)),
                ("message", models.TextField()),
                ("consent_given", models.BooleanField(default=False)),
                ("consent_given_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_processed", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
