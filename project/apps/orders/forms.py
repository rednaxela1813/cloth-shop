# apps/orders/forms.py
from django import forms

from .models import Order


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    email = forms.EmailField()
    phone = forms.CharField(max_length=40, required=False)

    country = forms.CharField(max_length=2)
    shipping_method = forms.ChoiceField(choices=Order.ShippingMethod.choices)
    region = forms.CharField(max_length=120, required=False)
    city = forms.CharField(max_length=120)
    postal_code = forms.CharField(max_length=20, required=False)
    address_line1 = forms.CharField(max_length=255)
    address_line2 = forms.CharField(max_length=255, required=False)

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
