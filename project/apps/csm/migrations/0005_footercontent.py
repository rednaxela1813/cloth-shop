from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("csm", "0004_homeherocontent"),
    ]

    operations = [
        migrations.CreateModel(
            name="FooterContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "description",
                    models.TextField(
                        default="Italian fashion marketplace: women, men, kids. Curated picks and fast delivery.",
                        verbose_name="Popis značky vo footeri",
                    ),
                ),
                ("shop_title", models.CharField(default="Shop", max_length=120, verbose_name="Nadpis sekcie Shop")),
                ("shop_women_label", models.CharField(default="Women", max_length=120, verbose_name="Text odkazu Women")),
                ("shop_men_label", models.CharField(default="Men", max_length=120, verbose_name="Text odkazu Men")),
                ("shop_kids_label", models.CharField(default="Kids", max_length=120, verbose_name="Text odkazu Kids")),
                ("shop_sale_label", models.CharField(default="Sale", max_length=120, verbose_name="Text odkazu Sale")),
                ("help_title", models.CharField(default="Help", max_length=120, verbose_name="Nadpis sekcie Help")),
                (
                    "help_customer_care_label",
                    models.CharField(default="Customer care", max_length=120, verbose_name="Text odkazu Customer care"),
                ),
                (
                    "help_returns_label",
                    models.CharField(default="Returns", max_length=120, verbose_name="Text odkazu Returns"),
                ),
                (
                    "help_contact_label",
                    models.CharField(default="Kontakt", max_length=120, verbose_name="Text odkazu Kontakt"),
                ),
                ("legal_title", models.CharField(default="Legal", max_length=120, verbose_name="Nadpis sekcie Legal")),
                (
                    "copyright_text",
                    models.CharField(
                        default="Deilmann s.r.o. All rights reserved.",
                        max_length=160,
                        verbose_name="Copyright text",
                    ),
                ),
                ("badge_primary", models.CharField(default="SK/EU ready", max_length=120, verbose_name="Prvý badge")),
                (
                    "badge_secondary",
                    models.CharField(default="Bezpečná platba", max_length=120, verbose_name="Druhý badge"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Aktualizované")),
            ],
            options={
                "verbose_name": "Obsah footer sekcie",
                "verbose_name_plural": "Obsah footer sekcie",
            },
        ),
    ]
