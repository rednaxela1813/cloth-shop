from __future__ import annotations

import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from faker import Faker

from apps.products.models import Category, Product, ProductCategory, ProductVariant


class Command(BaseCommand):
    help = "Generate a large fake catalog with root categories, subcategories, products, and variants."

    def add_arguments(self, parser):
        parser.add_argument("--categories", type=int, default=24, help="Number of root categories to create.")
        parser.add_argument(
            "--products-per-category",
            type=int,
            default=120,
            help="Number of products to create per root category.",
        )
        parser.add_argument(
            "--subcategories",
            type=int,
            default=4,
            help="Number of child categories to create for each root category.",
        )
        parser.add_argument(
            "--variants",
            type=int,
            default=3,
            help="Maximum number of variants per product.",
        )
        parser.add_argument("--seed", type=int, default=20260315, help="Deterministic random seed.")

    @transaction.atomic
    def handle(self, *args, **options):
        categories_count = max(1, options["categories"])
        products_per_category = max(1, options["products_per_category"])
        subcategories_per_root = max(0, options["subcategories"])
        max_variants = max(1, options["variants"])
        seed = options["seed"]

        fake = Faker()
        Faker.seed(seed)
        random.seed(seed)

        root_categories: list[Category] = []
        all_subcategories: dict[int, list[Category]] = {}

        for index in range(categories_count):
            root = Category.objects.create(
                name=self._category_name(fake, index=index),
                is_active=True,
                sort_order=index,
            )
            root_categories.append(root)

            children: list[Category] = []
            for child_index in range(subcategories_per_root):
                child = Category.objects.create(
                    name=self._subcategory_name(fake, root_name=root.name, index=child_index),
                    parent=root,
                    is_active=True,
                    sort_order=child_index,
                )
                children.append(child)
            all_subcategories[root.id] = children

        created_products = 0
        created_variants = 0

        for root in root_categories:
            children = all_subcategories[root.id]
            for product_index in range(products_per_category):
                product = Product.objects.create(
                    name=self._product_name(fake),
                    brand=fake.company(),
                    origin_country=random.choice(["Italy", "France", "Spain", "Portugal"]),
                    description=fake.paragraph(nb_sentences=3),
                    details="\n".join(fake.sentences(nb=4)),
                    is_active=True,
                    is_trending=random.random() < 0.08,
                )

                ProductCategory.objects.create(
                    product=product,
                    category=root,
                    is_primary=not children,
                )

                if children:
                    ProductCategory.objects.create(
                        product=product,
                        category=random.choice(children),
                        is_primary=True,
                    )

                variants_count = random.randint(1, max_variants)
                variant_options = random.sample(
                    [
                        (size, color)
                        for size in ["XS", "S", "M", "L", "XL", "32", "33", "34", "36", "38"]
                        for color in ["Black", "White", "Beige", "Brown", "Blue", "Red", "Green", "Grey", "Navy"]
                    ],
                    k=variants_count,
                )
                for variant_index in range(variants_count):
                    size, color = variant_options[variant_index]
                    price = self._price()
                    ProductVariant.objects.create(
                        product=product,
                        size=size,
                        color=color,
                        sku=self._sku(root=root, product=product, variant_index=variant_index),
                        price=price,
                        compare_at=self._compare_at(price=price),
                        stock=random.randint(0, 25),
                        is_active=True,
                    )
                    created_variants += 1

                created_products += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Created "
                f"{len(root_categories)} root categories, "
                f"{sum(len(items) for items in all_subcategories.values())} subcategories, "
                f"{created_products} products, "
                f"{created_variants} variants."
            )
        )

    def _category_name(self, fake: Faker, *, index: int) -> str:
        return f"{fake.unique.word().title()} {fake.unique.word().title()} {index + 1}"

    def _subcategory_name(self, fake: Faker, *, root_name: str, index: int) -> str:
        return f"{root_name} {fake.unique.word().title()} {index + 1}"

    def _product_name(self, fake: Faker) -> str:
        return f"{fake.color_name()} {fake.word().title()} {fake.word().title()}"

    def _sku(self, *, root: Category, product: Product, variant_index: int) -> str:
        root_part = str(root.public_id).replace("-", "")[:6].upper()
        product_part = str(product.public_id).replace("-", "")[:10].upper()
        return f"FC-{root_part}-{product_part}-{variant_index + 1}"

    def _price(self) -> Decimal:
        value = Decimal(random.randint(35, 450))
        cents = Decimal(random.choice([".00", ".90", ".50"]))
        return value + cents

    def _compare_at(self, *, price: Decimal) -> Decimal | None:
        if random.random() >= 0.2:
            return None
        uplift = Decimal(random.randint(10, 80))
        cents = Decimal(random.choice([".00", ".90", ".50"]))
        return price + uplift + cents
