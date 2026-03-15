# project/apps/catalog/management/commands/seed_categories.py
from django.core.management.base import BaseCommand

from apps.products.models import Category


class Command(BaseCommand):
    help = "Seed base categories (women/men/sale)."

    def handle(self, *args, **options):
        seeds = [
            {"name": "Women", "slug": "women", "sort_order": 1},
            {"name": "Men", "slug": "men", "sort_order": 2},
            {"name": "Sale", "slug": "sale", "sort_order": 3},
        ]

        for seed in seeds:
            obj, created = Category.objects.update_or_create(
                slug=seed["slug"],
                defaults={
                    "name": seed["name"],
                    "is_active": True,
                    "sort_order": seed["sort_order"],
                    "parent": None,
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} category: {obj.name} ({obj.slug})")
