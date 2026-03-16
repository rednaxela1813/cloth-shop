from __future__ import annotations

import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from faker import Faker

from apps.products.models import Category, Product, ProductCategory, ProductImage, ProductVariant


MANDATORY_ROOT_NAMES = ["Women", "Men", "Kids", "Sale"]
DEFAULT_TOTAL_CATEGORIES = 54
DEFAULT_PRODUCTS_PER_CATEGORY = 100
DEFAULT_ROOT_CATEGORIES = 24

SIZE_OPTIONS = ["XS", "S", "M", "L", "XL", "32", "33", "34", "36", "38"]
COLOR_OPTIONS = ["Black", "White", "Beige", "Brown", "Blue", "Red", "Green", "Grey", "Navy"]


class Command(BaseCommand):
    help = "Generate a large fake catalog with mandatory roots, extra categories, products, variants, category covers, and product images."

    def add_arguments(self, parser):
        parser.add_argument("--categories", type=int, default=DEFAULT_ROOT_CATEGORIES, help="Target number of root categories to create.")
        parser.add_argument(
            "--total-categories",
            type=int,
            default=DEFAULT_TOTAL_CATEGORIES,
            help="Total number of categories to create, including roots and subcategories.",
        )
        parser.add_argument(
            "--products-per-category",
            type=int,
            default=DEFAULT_PRODUCTS_PER_CATEGORY,
            help="Number of products to create per created category.",
        )
        parser.add_argument(
            "--subcategories",
            type=int,
            default=4,
            help="Minimum number of child categories to create per root when enough category budget is available.",
        )
        parser.add_argument(
            "--variants",
            type=int,
            default=3,
            help="Maximum number of variants per product.",
        )
        parser.add_argument("--seed", type=int, default=20260316, help="Deterministic random seed.")
        parser.add_argument(
            "--root-names",
            nargs="+",
            default=None,
            help="Optional extra root names. Mandatory roots Women Men Kids Sale are always created first.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        products_per_category = max(1, options["products_per_category"])
        max_variants = max(1, options["variants"])
        seed = options["seed"]

        fake = Faker()
        Faker.seed(seed)
        random.seed(seed)

        root_names = self._build_root_names(fake=fake, root_names=options["root_names"], target_roots=options["categories"])
        target_total_categories = max(len(root_names), options["total_categories"] or DEFAULT_TOTAL_CATEGORIES)
        minimum_children_per_root = max(0, options["subcategories"])

        root_categories: list[Category] = []
        child_categories_by_root_id: dict[int, list[Category]] = {}
        all_categories: list[Category] = []

        for index, root_name in enumerate(root_names):
            root = Category.objects.create(
                name=root_name,
                slug=self._root_slug(root_name=root_name, index=index),
                is_active=True,
                sort_order=index,
                cover_image_url=self._category_cover_url(label=root_name),
            )
            root_categories.append(root)
            child_categories_by_root_id[root.id] = []
            all_categories.append(root)

        remaining_categories = max(0, target_total_categories - len(all_categories))
        remaining_categories = self._create_minimum_children(
            fake=fake,
            roots=root_categories,
            child_categories_by_root_id=child_categories_by_root_id,
            all_categories=all_categories,
            remaining_categories=remaining_categories,
            minimum_children_per_root=minimum_children_per_root,
        )
        self._create_remaining_children(
            fake=fake,
            roots=root_categories,
            child_categories_by_root_id=child_categories_by_root_id,
            all_categories=all_categories,
            remaining_categories=remaining_categories,
        )

        created_products = 0
        created_variants = 0
        created_images = 0

        for category in all_categories:
            root = category if category.parent_id is None else category.parent
            root_children = child_categories_by_root_id.get(root.id, [])

            for product_index in range(products_per_category):
                product = Product.objects.create(
                    name=self._product_name(fake=fake),
                    brand=fake.company(),
                    origin_country=random.choice(["Italy", "France", "Spain", "Portugal"]),
                    description=fake.paragraph(nb_sentences=3),
                    details="\n".join(fake.sentences(nb=4)),
                    is_active=True,
                    is_trending=random.random() < 0.08,
                )

                ProductCategory.objects.create(
                    product=product,
                    category=category,
                    is_primary=True,
                )

                if category.parent_id is None and root_children:
                    ProductCategory.objects.create(
                        product=product,
                        category=root_children[product_index % len(root_children)],
                        is_primary=False,
                    )

                ProductImage.objects.create(
                    product=product,
                    image_url=self._product_image_url(product=product, primary_category=category),
                    alt=product.name,
                    sort_order=0,
                    is_primary=True,
                )
                created_images += 1

                variants_count = random.randint(1, max_variants)
                variant_options = random.sample(
                    [(size, color) for size in SIZE_OPTIONS for color in COLOR_OPTIONS],
                    k=variants_count,
                )
                for variant_index, (size, color) in enumerate(variant_options):
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
                f"{sum(len(items) for items in child_categories_by_root_id.values())} subcategories, "
                f"{created_products} products, "
                f"{created_images} product images, "
                f"{created_variants} variants."
            )
        )

    def _build_root_names(self, *, fake: Faker, root_names: list[str] | None, target_roots: int) -> list[str]:
        names: list[str] = []
        for mandatory in MANDATORY_ROOT_NAMES:
            if mandatory not in names:
                names.append(mandatory)

        for name in root_names or []:
            cleaned = name.strip()
            if cleaned and cleaned not in names:
                names.append(cleaned)

        while len(names) < max(len(MANDATORY_ROOT_NAMES), target_roots):
            candidate = self._category_name(fake=fake, index=len(names))
            if candidate not in names:
                names.append(candidate)

        return names

    def _create_minimum_children(
        self,
        *,
        fake: Faker,
        roots: list[Category],
        child_categories_by_root_id: dict[int, list[Category]],
        all_categories: list[Category],
        remaining_categories: int,
        minimum_children_per_root: int,
    ) -> int:
        if remaining_categories <= 0 or minimum_children_per_root <= 0:
            return remaining_categories

        created_rounds = 0
        while remaining_categories > 0 and created_rounds < minimum_children_per_root:
            for root in roots:
                if remaining_categories <= 0:
                    break

                child = self._create_child_category(
                    fake=fake,
                    root=root,
                    index=len(child_categories_by_root_id[root.id]),
                )
                child_categories_by_root_id[root.id].append(child)
                all_categories.append(child)
                remaining_categories -= 1
            created_rounds += 1

        return remaining_categories

    def _create_remaining_children(
        self,
        *,
        fake: Faker,
        roots: list[Category],
        child_categories_by_root_id: dict[int, list[Category]],
        all_categories: list[Category],
        remaining_categories: int,
    ) -> None:
        root_index = 0
        while remaining_categories > 0:
            root = roots[root_index % len(roots)]
            child = self._create_child_category(
                fake=fake,
                root=root,
                index=len(child_categories_by_root_id[root.id]),
            )
            child_categories_by_root_id[root.id].append(child)
            all_categories.append(child)
            remaining_categories -= 1
            root_index += 1

    def _create_child_category(self, *, fake: Faker, root: Category, index: int) -> Category:
        child_name = self._subcategory_name(fake=fake, root_name=root.name, index=index)
        return Category.objects.create(
            name=child_name,
            parent=root,
            is_active=True,
            sort_order=index,
            cover_image_url=self._category_cover_url(label=f"{root.name}-{child_name}"),
        )

    def _root_slug(self, *, root_name: str, index: int) -> str:
        mapping = {
            "Women": "women",
            "Men": "men",
            "Kids": "kids",
            "Sale": "sale",
        }
        return mapping.get(root_name, f"root-{index + 1}")

    def _category_cover_url(self, *, label: str) -> str:
        seed = label.lower().replace(" ", "-")
        return f"https://picsum.photos/seed/category-{seed}/1200/900"

    def _product_image_url(self, *, product: Product, primary_category: Category) -> str:
        category_seed = primary_category.slug or str(primary_category.public_id)
        product_seed = str(product.public_id).replace("-", "")[:12].lower()
        return f"https://picsum.photos/seed/product-{category_seed}-{product_seed}/900/1200"

    def _category_name(self, *, fake: Faker, index: int) -> str:
        return f"{fake.unique.word().title()} {fake.unique.word().title()} {index + 1}"

    def _subcategory_name(self, *, fake: Faker, root_name: str, index: int) -> str:
        return f"{root_name} {fake.unique.word().title()} {index + 1}"

    def _product_name(self, *, fake: Faker) -> str:
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
