from django import forms
from django.forms import modelform_factory
from django.contrib import admin
from apps.seo.models import SeoMeta
from .models import Category, Product, ProductCategory, ProductImage, ProductVariant, VariantImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    can_delete = False
    fields = ("image_url", "image_original", "image_card", "image_thumb", "alt", "sort_order", "is_primary")
    readonly_fields = ()
    ordering = ("sort_order", "id")


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
    fields = ("image_original", "image_card", "image_thumb", "alt", "sort_order", "is_primary")
    ordering = ("sort_order", "id")


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
        self._add_seo_fields()
        self._init_seo_fields()


@admin.register(Product)
class ProductAdmin(SeoMetaAdminMixin, admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ("name", "brand", "price", "is_active", "is_trending", "created")
    list_filter = ("is_active", "is_trending", "brand")
    search_fields = ("name", "brand", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductCategoryInline, ProductImageInline, ProductVariantInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "brand", "price", "compare_at")}),
        ("Status", {"fields": ("is_active", "is_trending")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords", "seo_og_image")}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        form._save_seo_fields(obj)

    def has_delete_permission(self, request, obj=None):
        return False


class CategoryProductInline(admin.TabularInline):
    model = ProductCategory
    fk_name = "category"
    extra = 1
    can_delete = False
    fields = ("product", "is_primary", "sort_order")
    ordering = ("sort_order", "id")


class CategoryAdminForm(SeoMetaFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].label = "Nadradená kategória (podkategória, voliteľné)"
        self.fields["parent"].help_text = "Vyberte nadradenú kategóriu, ak ide o podkategóriu."
        if self.instance and self.instance.pk:
            self.fields["parent"].queryset = self.fields["parent"].queryset.exclude(pk=self.instance.pk)
        self._add_seo_fields()
        self._init_seo_fields()


@admin.register(Category)
class CategoryAdmin(SeoMetaAdminMixin, admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ("name", "parent", "is_active", "sort_order", "created")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CategoryProductInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "parent", "is_active", "sort_order")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords", "seo_og_image")}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        form._save_seo_fields(obj)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("product", "category", "is_primary", "sort_order", "created")
    list_filter = ("is_primary", "category")
    search_fields = ("product__name", "category__name")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "sort_order", "created")
    list_filter = ("is_primary",)
    search_fields = ("product__name", "alt", "image_url")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "size", "color", "sku", "price", "stock", "is_active")
    list_filter = ("is_active", "color", "size")
    search_fields = ("product__name", "sku")
    inlines = [VariantImageInline]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VariantImage)
class VariantImageAdmin(admin.ModelAdmin):
    list_display = ("variant", "is_primary", "sort_order", "created")
    list_filter = ("is_primary",)
    search_fields = ("variant__sku", "variant__product__name", "alt")

    def has_delete_permission(self, request, obj=None):
        return False
