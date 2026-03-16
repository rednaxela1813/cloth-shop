# apps/orders/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Order


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=120, label=_("Meno a priezvisko"))
    email = forms.EmailField(label=_("E-mail"))
    phone = forms.CharField(max_length=40, required=False, label=_("Telefón"))

    country = forms.CharField(max_length=2, label=_("Krajina"))
    shipping_method = forms.ChoiceField(choices=Order.ShippingMethod.choices, label=_("Spôsob dopravy"))
    region = forms.CharField(max_length=120, required=False, label=_("Región"))
    city = forms.CharField(max_length=120, label=_("Mesto"))
    postal_code = forms.CharField(max_length=20, required=False, label=_("PSČ"))
    address_line1 = forms.CharField(max_length=255, label=_("Adresa, riadok 1"))
    address_line2 = forms.CharField(max_length=255, required=False, label=_("Adresa, riadok 2"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply consistent styling without repeating classes in templates.
        base_class = (
            "w-full rounded-md border border-zinc-300 px-3 py-2 text-sm "
            "focus:outline-none focus:ring-2 focus:ring-zinc-900"
        )
        error_class = (
            "w-full rounded-md border border-red-400 bg-red-50 px-3 py-2 text-sm text-zinc-900 "
            "focus:outline-none focus:ring-2 focus:ring-red-500"
        )

        for name, field in self.fields.items():
            field.widget.attrs.setdefault(
                "class",
                base_class,
            )

        if self.is_bound:
            self.errors
            for name, field in self.fields.items():
                if name not in self.errors:
                    continue
                field.widget.attrs["class"] = error_class
                field.widget.attrs["aria-invalid"] = "true"
                field.widget.attrs["aria-describedby"] = f"{name.replace('_', '-')}-error"
