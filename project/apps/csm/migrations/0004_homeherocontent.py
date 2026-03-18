from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("csm", "0003_sitebranding"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomeHeroContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("eyebrow", models.CharField(default="Vždy ako výpredaj", max_length=120, verbose_name="Krátky nadpis")),
                (
                    "title",
                    models.CharField(
                        default="Talianska móda. Luxusné značky. Férové ceny.",
                        max_length=255,
                        verbose_name="Hlavný nadpis",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        default="Vyberajte z kurátorskeho katalógu dámskej, pánskej a detskej módy – s rýchlym doručením a dôrazom na autenticitu.",
                        verbose_name="Popis",
                    ),
                ),
                (
                    "primary_cta_label",
                    models.CharField(default="Dámska móda", max_length=120, verbose_name="Text prvého tlačidla"),
                ),
                (
                    "secondary_cta_label",
                    models.CharField(default="Pánska móda", max_length=120, verbose_name="Text druhého tlačidla"),
                ),
                (
                    "tertiary_cta_label",
                    models.CharField(default="Výber zľav", max_length=120, verbose_name="Text tretieho tlačidla"),
                ),
                (
                    "delivery_title",
                    models.CharField(default="Doručenie", max_length=120, verbose_name="Nadpis výhody doručenia"),
                ),
                (
                    "delivery_text",
                    models.CharField(
                        default="Express (typicky 2–4 pracovné dni)",
                        max_length=160,
                        verbose_name="Text výhody doručenia",
                    ),
                ),
                (
                    "authenticity_title",
                    models.CharField(default="Autenticita", max_length=120, verbose_name="Nadpis výhody autenticity"),
                ),
                (
                    "authenticity_text",
                    models.CharField(
                        default="Overenie predajcom + platformou",
                        max_length=160,
                        verbose_name="Text výhody autenticity",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Aktualizované")),
            ],
            options={
                "verbose_name": "Obsah hero sekcie",
                "verbose_name_plural": "Obsah hero sekcie",
            },
        ),
    ]
