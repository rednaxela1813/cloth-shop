from django import forms
from django.forms import modelform_factory
from django.contrib import admin
from django.db.models import Prefetch
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from apps.seo.models import SeoMeta
from .models import Category, Product, ProductCategory, ProductImage, ProductVariant, VariantImage

LOW_STOCK_THRESHOLD = 3


class AdminImagePreviewMixin:
    preview_width = 120

    def _render_image_preview(self, field_file):
        if not field_file:
            return _("Bez obrázka")
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

    @admin.display(description=_("Náhľad originálu"))
    def image_original_preview(self, obj):
        return AdminImagePreviewMixin()._render_image_preview(obj.image_original)

    @admin.display(description=_("Náhľad karty"))
    def image_card_preview(self, obj):
        return AdminImagePreviewMixin()._render_image_preview(obj.image_card)

    @admin.display(description=_("Náhľad miniatúry"))
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

    @admin.display(description=_("Náhľad originálu"))
    def image_original_preview(self, obj):
        return AdminImagePreviewMixin()._render_image_preview(obj.image_original)

    @admin.display(description=_("Náhľad karty"))
    def image_card_preview(self, obj):
        return AdminImagePreviewMixin()._render_image_preview(obj.image_card)

    @admin.display(description=_("Náhľad miniatúry"))
    def image_thumb_preview(self, obj):
        return AdminImagePreviewMixin()._render_image_preview(obj.image_thumb)


class StockLevelFilter(admin.SimpleListFilter):
    title = _("Sklad")
    parameter_name = "stock_level"

    def lookups(self, request, model_admin):
        return (
            ("out", _("Vypredané")),
            ("low", _("Nízky stav")),
            ("available", _("Na sklade")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "out":
            return queryset.filter(stock=0)
        if value == "low":
            return queryset.filter(stock__gt=0, stock__lte=LOW_STOCK_THRESHOLD)
        if value == "available":
            return queryset.filter(stock__gt=LOW_STOCK_THRESHOLD)
        return queryset


class SeoMetaFormMixin:
    def _add_seo_fields(self):
        self.fields["seo_title"] = forms.CharField(label=_("SEO titulok"), max_length=255, required=False)
        self.fields["seo_description"] = forms.CharField(
            label=_("SEO popis"),
            required=False,
            widget=forms.Textarea(attrs={"rows": 3}),
        )
        self.fields["seo_keywords"] = forms.CharField(label=_("SEO kľúčové slová"), max_length=512, required=False)
        self.fields["seo_og_image"] = forms.ImageField(label=_("SEO OG obrázok"), required=False)

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
        (_("Stav"), {"fields": ("is_active", "is_trending")}),
        (_("SEO"), {"fields": ("seo_title", "seo_description", "seo_keywords", "seo_og_image", "seo_og_image_preview")}),
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

    @admin.display(description=_("Cena"))
    def display_price_admin(self, obj):
        return obj.display_price

    @admin.display(description=_("Aktuálny OG obrázok"))
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
    verbose_name = _("Podkategória")
    verbose_name_plural = _("Podkategórie")
    fields = ("name", "is_active", "sort_order")
    ordering = ("sort_order", "name", "id")
    show_change_link = True


class CategoryAdminForm(SeoMetaFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].label = _("Nadradená kategória")
        self.fields["parent"].help_text = _(
            "Nechajte prázdne pre hlavnú kategóriu. Nadradenú kategóriu vyberte len pri vytváraní podkategórie."
        )
        parent_queryset = self.fields["parent"].queryset.order_by("name", "id")
        if self.instance and self.instance.pk:
            parent_queryset = parent_queryset.exclude(pk=self.instance.pk)
        self.fields["parent"].queryset = parent_queryset
        self._add_seo_fields()
        self._init_seo_fields()


@admin.register(Category)
class CategoryAdmin(SeoMetaAdminMixin, admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ("name", "parent", "is_active", "cover_image", "cover_image_url", "sort_order", "created")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CategoryChildInline, CategoryProductInline]
    list_select_related = ("parent",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "parent", "is_active", "sort_order")}),
        (_("Titulný obrázok"), {"fields": ("cover_image", "cover_image_url")}),
        (_("SEO"), {"fields": ("seo_title", "seo_description", "seo_keywords", "seo_og_image")}),
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
    list_display = ("product", "size", "color", "sku", "price", "stock", "stock_status", "is_active")
    list_filter = (StockLevelFilter, "is_active", "color", "size")
    search_fields = ("product__name", "sku")
    inlines = [VariantImageInline]
    list_select_related = ("product",)

    @admin.display(description=_("Stav skladu"))
    def stock_status(self, obj):
        if obj.stock <= 0:
            return _("Vypredané")
        if obj.stock <= LOW_STOCK_THRESHOLD:
            return _("Nízky stav")
        return _("Na sklade")

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
