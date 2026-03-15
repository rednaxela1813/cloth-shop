from django import forms
from django.forms import modelform_factory
from django.contrib import admin
from django.db.models import Prefetch
from django.utils.html import format_html
from apps.seo.models import SeoMeta
from .models import Category, Product, ProductCategory, ProductImage, ProductVariant, VariantImage


class AdminImagePreviewMixin:
    preview_width = 120

    def _render_image_preview(self, field_file):
        if not field_file:
            return "No image"
        return format_html(
            '<img src="{}" alt="" style="max-width: {}px; max-height: {}px; object-fit: cover; border-radius: 6px; border: 1px solid #ddd;" />',
            field_file.url,
            self.preview_width,
            self.preview_width,
        )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    can_delete = False
    fields = (
        "image_url",
        "image_original",
        "image_original_preview",
        "image_card",
        "image_card_preview",
        "image_thumb",
        "image_thumb_preview",
        "alt",
        "sort_order",
        "is_primary",
    )
    readonly_fields = ("image_original_preview", "image_card_preview", "image_thumb_preview")
    ordering = ("sort_order", "id")

    @admin.display(description="Original preview")
    def image_original_preview(self, obj):
        return AdminImagePreviewMixin()._render_image_preview(obj.image_original)

    @admin.display(description="Card preview")
    def image_card_preview(self, obj):
        return AdminImagePreviewMixin()._render_image_preview(obj.image_card)

    @admin.display(description="Thumb preview")
    def image_thumb_preview(self, obj):
        return AdminImagePreviewMixin()._render_image_preview(obj.image_thumb)


class ProductCategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 1
    can_delete = False
    fields = ("category", "is_primary", "sort_order")
    ordering = ("sort_order", "id")


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    can_delete = False
    fields = ("public_id", "size", "color", "sku", "price", "compare_at", "stock", "is_active")
    readonly_fields = ("public_id",)
    ordering = ("id",)


class VariantImageInline(admin.TabularInline):
    model = VariantImage
    extra = 1
    can_delete = False
    fields = (
        "image_original",
        "image_original_preview",
        "image_card",
        "image_card_preview",
        "image_thumb",
        "image_thumb_preview",
        "alt",
        "sort_order",
        "is_primary",
    )
    readonly_fields = ("image_original_preview", "image_card_preview", "image_thumb_preview")
    ordering = ("sort_order", "id")

    @admin.display(description="Original preview")
    def image_original_preview(self, obj):
        return AdminImagePreviewMixin()._render_image_preview(obj.image_original)

    @admin.display(description="Card preview")
    def image_card_preview(self, obj):
        return AdminImagePreviewMixin()._render_image_preview(obj.image_card)

    @admin.display(description="Thumb preview")
    def image_thumb_preview(self, obj):
        return AdminImagePreviewMixin()._render_image_preview(obj.image_thumb)


class SeoMetaFormMixin:
    def _add_seo_fields(self):
        self.fields["seo_title"] = forms.CharField(label="SEO title", max_length=255, required=False)
        self.fields["seo_description"] = forms.CharField(
            label="SEO description",
            required=False,
            widget=forms.Textarea(attrs={"rows": 3}),
        )
        self.fields["seo_keywords"] = forms.CharField(label="SEO keywords", max_length=512, required=False)
        self.fields["seo_og_image"] = forms.ImageField(label="SEO OG image", required=False)

    def _init_seo_fields(self):
        seo = getattr(self.instance, "seo_meta", None)
        if not seo:
            return
        self.fields["seo_title"].initial = seo.title
        self.fields["seo_description"].initial = seo.description
        self.fields["seo_keywords"].initial = seo.keywords
        self.fields["seo_og_image"].initial = seo.og_image

    def _save_seo_fields(self, instance):
        title = self.cleaned_data.get("seo_title", "")
        description = self.cleaned_data.get("seo_description", "")
        keywords = self.cleaned_data.get("seo_keywords", "")
        og_image = self.cleaned_data.get("seo_og_image")

        if not any([title, description, keywords, og_image]) and not instance.seo_meta:
            return

        seo = instance.seo_meta or SeoMeta()
        seo.title = title or ""
        seo.description = description or ""
        seo.keywords = keywords or ""
        if og_image:
            seo.og_image = og_image
        seo.save()

        if instance.seo_meta_id != seo.id:
            instance.seo_meta = seo
            instance.save(update_fields=["seo_meta"])


class SeoMetaAdminMixin:
    def get_form(self, request, obj=None, **kwargs):
        kwargs.pop("change", None)
        kwargs.pop("fields", None)
        defaults = {
            "form": self.form,
            "fields": None,
            "exclude": self.get_exclude(request, obj),
        }
        defaults.update(kwargs)
        return modelform_factory(self.model, **defaults)


class ProductAdminForm(SeoMetaFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["origin_country"].widget = forms.TextInput()
        self.fields["description"].widget = forms.Textarea(attrs={"rows": 5})
        self.fields["details"].widget = forms.Textarea(attrs={"rows": 5})
        self._add_seo_fields()
        self._init_seo_fields()


@admin.register(Product)
class ProductAdmin(AdminImagePreviewMixin, SeoMetaAdminMixin, admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ("name", "brand", "display_price_admin", "is_active", "is_trending", "created")
    list_filter = ("is_active", "is_trending", "brand")
    search_fields = ("name", "brand", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductCategoryInline, ProductImageInline, ProductVariantInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "brand", "origin_country", "description", "details")}),
        ("Status", {"fields": ("is_active", "is_trending")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords", "seo_og_image", "seo_og_image_preview")}),
    )
    readonly_fields = ("seo_og_image_preview",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                Prefetch(
                    "variants",
                    queryset=ProductVariant.objects.filter(is_active=True).order_by("price", "id"),
                    to_attr="_prefetched_active_variants_for_pricing",
                )
            )
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        form._save_seo_fields(obj)

    @admin.display(description="Price")
    def display_price_admin(self, obj):
        return obj.display_price

    @admin.display(description="Current OG image")
    def seo_og_image_preview(self, obj):
        seo = getattr(obj, "seo_meta", None)
        return self._render_image_preview(seo.og_image if seo else None)

    def has_delete_permission(self, request, obj=None):
        return False


class CategoryProductInline(admin.TabularInline):
    model = ProductCategory
    fk_name = "category"
    extra = 1
    can_delete = False
    fields = ("product", "is_primary", "sort_order")
    ordering = ("sort_order", "id")


class CategoryChildInline(admin.TabularInline):
    model = Category
    fk_name = "parent"
    extra = 1
    verbose_name = "Subcategory"
    verbose_name_plural = "Subcategories"
    fields = ("name", "is_active", "sort_order")
    ordering = ("sort_order", "name", "id")
    show_change_link = True


class CategoryAdminForm(SeoMetaFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].label = "Parent category"
        self.fields["parent"].help_text = "Leave empty for a top-level category. Select a parent only when creating a subcategory."
        parent_queryset = self.fields["parent"].queryset.order_by("name", "id")
        if self.instance and self.instance.pk:
            parent_queryset = parent_queryset.exclude(pk=self.instance.pk)
        self.fields["parent"].queryset = parent_queryset
        self._add_seo_fields()
        self._init_seo_fields()


@admin.register(Category)
class CategoryAdmin(SeoMetaAdminMixin, admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ("name", "parent", "is_active", "sort_order", "created")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CategoryChildInline, CategoryProductInline]
    list_select_related = ("parent",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "parent", "is_active", "sort_order")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords", "seo_og_image")}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        form._save_seo_fields(obj)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("product", "category", "is_primary", "sort_order", "created")
    list_filter = ("is_primary", "category")
    search_fields = ("product__name", "category__name")
    list_select_related = ("product", "category")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "sort_order", "created")
    list_filter = ("is_primary",)
    search_fields = ("product__name", "alt", "image_url")
    list_select_related = ("product",)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "size", "color", "sku", "price", "stock", "is_active")
    list_filter = ("is_active", "color", "size")
    search_fields = ("product__name", "sku")
    inlines = [VariantImageInline]
    list_select_related = ("product",)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VariantImage)
class VariantImageAdmin(admin.ModelAdmin):
    list_display = ("variant", "is_primary", "sort_order", "created")
    list_filter = ("is_primary",)
    search_fields = ("variant__sku", "variant__product__name", "alt")
    list_select_related = ("variant", "variant__product")

    def has_delete_permission(self, request, obj=None):
        return False
