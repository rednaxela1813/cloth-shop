#project/apps/products/models.py
from __future__ import annotations
import uuid

from django.db import models


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def trending(self):
        return self.active().filter(is_trending=True).order_by("-created")

    def in_category(self, category):
        return self.active().filter(categories=category).order_by("-created").distinct()
    

class CategoryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def roots(self):
        return self.active().filter(parent__isnull=True).order_by("sort_order", "name", "id")


class Product(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    seo_meta = models.OneToOneField("seo.SeoMeta", on_delete=models.CASCADE, null=True, blank=True)
    
    brand = models.CharField(max_length=120, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    compare_at = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_trending = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField("Category", through="ProductCategory", related_name="products", blank=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            # Slug policy вынесен в service-layer для единообразия доменных правил.
            from apps.products.services.slug_service import generate_unique_slug

            self.slug = generate_unique_slug(model_cls=Product, source_value=self.name, fallback="product")
        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        primary = self.images.filter(is_primary=True).order_by("sort_order", "id").first()
        if primary:
            return primary
        return self.images.order_by("sort_order", "id").first()

    def _pricing_variants(self):
        # Use prefetched variants when available to avoid N+1 on listing pages.
        prefetched = getattr(self, "_prefetched_active_variants_for_pricing", None)
        if prefetched is not None:
            return prefetched
        return list(self.variants.filter(is_active=True).order_by("price", "id"))

    @property
    def lowest_priced_variant(self):
        variants = self._pricing_variants()
        return variants[0] if variants else None

    @property
    def display_price(self):
        lowest = self.lowest_priced_variant
        if lowest:
            return lowest.price
        return self.price

    @property
    def display_compare_at(self):
        lowest = self.lowest_priced_variant
        if lowest:
            return lowest.compare_at
        return self.compare_at

    @property
    def default_variant(self):
        return self.variants.filter(is_active=True).order_by("-stock", "id").first()
    
    @property
    def primary_category(self):
        """
        Возвращает Category для breadcrumbs/SEO.

        Правило:
        1) если есть связь ProductCategory.is_primary=True -> берём её
        2) иначе берём первую связь по sort_order/id
        3) если связей нет -> None
        """
        link = (
            self.category_links.select_related("category")
            .filter(category__is_active=True, is_primary=True)
            .order_by("sort_order", "id")
            .first()
        )
        if link:
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
            models.Index(fields=["product", "is_active"]),
            models.Index(fields=["sku"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} — {self.size} / {self.color}"

    @property
    def primary_image(self):
        primary = self.images.filter(is_primary=True).order_by("sort_order", "id").first()
        if primary:
            return primary
        return self.images.order_by("sort_order", "id").first()

    @property
    def cart_image(self):
        variant_image = self.primary_image
        if variant_image:
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
        # Инвариант primary вынесен в service-layer, чтобы модель оставалась тонкой.
        from apps.products.services.variant_image_service import enforce_single_primary_variant_image

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
        """
        Enforce-инвариант:
        - если эта связь primary, то все остальные связи этого товара primary=False
        Делается после сохранения, чтобы у объекта был id и фильтр exclude(id=...) работал.
        """
        super().save(*args, **kwargs)
        # Инвариант вынесен в service-layer для снижения связанности модели.
        from apps.products.services.product_category_service import enforce_single_primary_product_category

        enforce_single_primary_product_category(self)




class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")

    # оставляем на будущее, но пока не используем:
    image_url = models.URLField(max_length=1000, blank=True)

    # три версии, которые реально будет использовать фронт
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
        # Тяжелая обработка изображений вынесена в service-layer (PR2).
        from apps.products.services.product_image_service import process_product_image_after_save

        process_product_image_after_save(self)




class Category(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    seo_meta = models.OneToOneField("seo.SeoMeta", on_delete=models.SET_NULL, null=True, blank=True)

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

    def save(self, *args, **kwargs):
        # Генерируем slug один раз при создании (или если поле пустое)
        if not self.slug:
            from apps.products.services.slug_service import generate_unique_slug

            self.slug = generate_unique_slug(model_cls=Category, source_value=self.name, fallback="category")
        super().save(*args, **kwargs)
