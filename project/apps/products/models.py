# project/apps/products/models.py
from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import models


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def trending(self):
        return self.active().filter(is_trending=True).order_by("-created", "-id")

    def with_listing_related(self):
        """
        Базовая заготовка для витринных списков.
        Сюда лучше добавлять prefetch/select_related в use-case слое,
        но этот метод полезен как единая точка входа.
        """
        return self.active()

    def in_category(self, category):
        """
        Фильтрация по категории и её потомкам.

        Важно:
        self_and_descendants() у Category сейчас не самый эффективный способ
        для больших деревьев, но оставляем совместимость с текущей архитектурой.
        """
        return (
            self.active()
            .filter(categories__in=category.self_and_descendants())
            .distinct()
            .order_by("-created", "-id")
        )


class CategoryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def roots(self):
        return self.active().filter(parent__isnull=True).order_by("sort_order", "name", "id")


class Product(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    seo_meta = models.OneToOneField(
        "seo.SeoMeta",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    brand = models.CharField(max_length=120, blank=True)
    origin_country = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    details = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    is_trending = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    categories = models.ManyToManyField(
        "Category",
        through="ProductCategory",
        related_name="products",
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created", "-id"]
        indexes = [
            models.Index(fields=["is_active", "-created"]),
            models.Index(fields=["is_active", "brand"]),
            models.Index(fields=["is_trending", "-created"]),
            models.Index(fields=["brand"]),
        ]

    def __init__(self, *args, **kwargs):
        """
        Временная совместимость со старым кодом, где product-level pricing
        ещё мог передаваться при инициализации модели.
        """
        kwargs.pop("price", None)
        kwargs.pop("compare_at", None)
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from apps.products.services.slug_service import generate_unique_slug

            self.slug = generate_unique_slug(
                model_cls=Product,
                source_value=self.name,
                fallback="product",
            )
        super().save(*args, **kwargs)

    def _sorted_prefetched_images(self):
        """
        Возвращает prefetched images в стабильном порядке, если они уже были
        загружены заранее. Иначе None.
        """
        prefetched_images = getattr(self, "_prefetched_images_for_listing", None)
        if prefetched_images is not None:
            return sorted(prefetched_images, key=lambda image: (image.sort_order, image.id))

        cache = getattr(self, "_prefetched_objects_cache", None) or {}
        images = cache.get("images")
        if images is None:
            return None

        return sorted(images, key=lambda image: (image.sort_order, image.id))

    @property
    def primary_image(self):
        """
        Возвращает основное изображение товара.

        Порядок:
        1) если изображения уже prefetched — работаем только в памяти;
        2) ищем primary среди prefetched;
        3) иначе fallback на первый prefetched;
        4) если prefetch не было — обращаемся к БД.
        """
        prefetched_images = self._sorted_prefetched_images()
        if prefetched_images is not None:
            primary = next((image for image in prefetched_images if image.is_primary), None)
            return primary or (prefetched_images[0] if prefetched_images else None)

        primary = self.images.filter(is_primary=True).order_by("sort_order", "id").first()
        if primary is not None:
            return primary

        return self.images.order_by("sort_order", "id").first()

    def _pricing_variants(self):
        """
        Возвращает активные варианты товара, отсортированные по цене.
        Если варианты уже prefetched, повторно в БД не ходим.
        """
        prefetched = getattr(self, "_prefetched_active_variants_for_pricing", None)
        if prefetched is not None:
            return prefetched

        return list(self.variants.filter(is_active=True).order_by("price", "id"))

    def _active_variants_for_default_selection(self):
        """
        Возвращает активные варианты для выбора default_variant.
        Если варианты уже prefetched, повторно в БД не ходим.
        """
        prefetched = getattr(self, "_prefetched_active_variants_for_pricing", None)
        if prefetched is not None:
            return prefetched

        return list(self.variants.filter(is_active=True).order_by("-stock", "id"))

    @property
    def lowest_priced_variant(self):
        variants = self._pricing_variants()
        return variants[0] if variants else None

    @property
    def display_price(self):
        lowest = self.lowest_priced_variant
        return lowest.price if lowest else None

    @property
    def display_compare_at(self):
        lowest = self.lowest_priced_variant
        return lowest.compare_at if lowest else None

    @property
    def default_variant(self):
        """
        Предпочитаем вариант с наибольшим stock.
        При равенстве — меньший id.
        """
        variants = self._active_variants_for_default_selection()
        if not variants:
            return None

        return min(variants, key=lambda variant: (-variant.stock, variant.id))

    @property
    def primary_category(self):
        """
        Возвращает Category для breadcrumbs/SEO.

        Правило:
        1) если есть ProductCategory.is_primary=True -> берём её;
        2) иначе берём первую связь по sort_order/id;
        3) если связей нет -> None.

        Важно:
        если category_links не prefetched, это свойство может дать N+1
        на списочных страницах. Для listings лучше заранее делать prefetch.
        """
        prefetched_links = getattr(self, "_prefetched_primary_category_links", None)
        if prefetched_links is not None:
            primary_link = next((link for link in prefetched_links if link.is_primary), None)
            if primary_link is not None:
                return primary_link.category
            return prefetched_links[0].category if prefetched_links else None

        cache = getattr(self, "_prefetched_objects_cache", None) or {}
        category_links = cache.get("category_links")
        if category_links is not None:
            category_links = sorted(category_links, key=lambda link: (link.sort_order, link.id))
            active_links = [link for link in category_links if getattr(link.category, "is_active", False)]
            primary_link = next((link for link in active_links if link.is_primary), None)
            if primary_link is not None:
                return primary_link.category
            return active_links[0].category if active_links else None

        link = (
            self.category_links.select_related("category")
            .filter(category__is_active=True, is_primary=True)
            .order_by("sort_order", "id")
            .first()
        )
        if link is not None:
            return link.category

        link = (
            self.category_links.select_related("category")
            .filter(category__is_active=True)
            .order_by("sort_order", "id")
            .first()
        )
        return link.category if link else None


class ProductVariant(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")

    size = models.CharField(max_length=32)
    color = models.CharField(max_length=64)
    sku = models.CharField(max_length=64, unique=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    compare_at = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["product", "id"]
        constraints = [
            models.UniqueConstraint(fields=["product", "size", "color"], name="uniq_variant_size_color"),
        ]
        indexes = [
            
            models.Index(fields=["product", "is_active", "price"]),
            models.Index(fields=["product", "is_active", "stock"]),
            models.Index(fields=["sku"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} — {self.size} / {self.color}"

    def _prefetched_images(self):
        cache = getattr(self, "_prefetched_objects_cache", None) or {}
        images = cache.get("images")
        if images is None:
            return None
        return sorted(images, key=lambda image: (image.sort_order, image.id))

    @property
    def primary_image(self):
        prefetched_images = self._prefetched_images()
        if prefetched_images is not None:
            primary = next((image for image in prefetched_images if image.is_primary), None)
            return primary or (prefetched_images[0] if prefetched_images else None)

        primary = self.images.filter(is_primary=True).order_by("sort_order", "id").first()
        if primary is not None:
            return primary

        return self.images.order_by("sort_order", "id").first()

    @property
    def cart_image(self):
        variant_image = self.primary_image
        if variant_image is not None:
            return variant_image
        return self.product.primary_image


class VariantImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="images")

    image_original = models.ImageField(upload_to="products/variants/original/", blank=True, null=True)
    image_card = models.ImageField(upload_to="products/variants/card/", blank=True, null=True)
    image_thumb = models.ImageField(upload_to="products/variants/thumb/", blank=True, null=True)

    alt = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["variant", "is_primary"]),
            models.Index(fields=["variant", "sort_order"]),
        ]

    def __str__(self) -> str:
        return f"{self.variant} — image"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        from apps.products.services.variant_image_service import (
            enforce_single_primary_variant_image,
        )

        enforce_single_primary_variant_image(self)


class ProductCategory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="category_links")
    category = models.ForeignKey("Category", on_delete=models.PROTECT, related_name="product_links")

    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["product", "category"], name="uniq_product_category"),
        ]
        indexes = [
            models.Index(fields=["product", "is_primary"]),
            models.Index(fields=["product", "sort_order"]),
            models.Index(fields=["category", "product"]),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        from apps.products.services.product_category_service import (
            enforce_single_primary_product_category,
        )

        enforce_single_primary_product_category(self)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")

    image_url = models.URLField(max_length=1000, blank=True)

    image_original = models.ImageField(upload_to="products/original/", blank=True, null=True)
    image_card = models.ImageField(upload_to="products/card/", blank=True, null=True)
    image_thumb = models.ImageField(upload_to="products/thumb/", blank=True, null=True)

    alt = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["product", "is_primary"]),
            models.Index(fields=["product", "sort_order"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} — image"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        from apps.products.services.product_image_service import process_product_image_after_save

        process_product_image_after_save(self)


class Category(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    seo_meta = models.OneToOneField(
        "seo.SeoMeta",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="children",
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        ordering = ["sort_order", "name", "id"]
        indexes = [
            models.Index(fields=["parent", "sort_order"]),
            models.Index(fields=["is_active", "sort_order"]),
        ]

    def __str__(self) -> str:
        return self.name

    def self_and_descendants(self):
        """
        Возвращает queryset из текущей категории и всех потомков.

        Это рабочая, но не идеальная реализация:
        она делает серию SQL-запросов по уровням дерева.
        Для больших деревьев категорий стоит перейти на MPTT/treebeard
        или materialized path.
        """
        ids = [self.id]
        frontier = [self.id]

        while frontier:
            child_ids = list(
                Category.objects.filter(parent_id__in=frontier).values_list("id", flat=True)
            )
            if not child_ids:
                break
            ids.extend(child_ids)
            frontier = child_ids

        return Category.objects.filter(id__in=ids)

    def clean(self):
        super().clean()

        if not self.parent_id:
            return

        if self.pk and self.parent_id == self.pk:
            raise ValidationError({"parent": "Category cannot be parent of itself."})

        ancestor = self.parent
        while ancestor is not None:
            if self.pk and ancestor.pk == self.pk:
                raise ValidationError({"parent": "Cyclic category hierarchy is not allowed."})
            ancestor = ancestor.parent

    def save(self, *args, **kwargs):
        if not self.slug:
            from apps.products.services.slug_service import generate_unique_slug

            self.slug = generate_unique_slug(
                model_cls=Category,
                source_value=self.name,
                fallback="category",
            )

        super().save(*args, **kwargs)