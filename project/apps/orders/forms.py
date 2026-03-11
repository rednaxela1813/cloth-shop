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
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-md border border-zinc-300 px-3 py-2 text-sm "
                "focus:outline-none focus:ring-2 focus:ring-zinc-900",
            )
