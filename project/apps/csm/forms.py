from django import forms

from .models import ContactMessage, MESSENGER_CHOICES


class ContactMessageForm(forms.ModelForm):
    consent = forms.BooleanField(
        required=True,
        label=(
            "Súhlasím so spracovaním osobných údajov podľa pravidiel EÚ "
            "na účely odpovede na moju správu."
        ),
    )

    class Meta:
        model = ContactMessage
        fields = [
            "name",
            "email",
            "messenger_type",
            "messenger_handle",
            "message",
        ]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = (
            "mt-2 w-full rounded-xl border border-zinc-300 bg-white px-4 py-2 text-sm "
            "focus:outline-none focus:ring-2 focus:ring-zinc-900"
        )
        self.fields["name"].required = False
        self.fields["name"].widget.attrs["class"] = base_classes
        self.fields["name"].widget.attrs["placeholder"] = "Ricotti customer"
        self.fields["email"].widget.attrs["class"] = base_classes
        self.fields["email"].widget.attrs["placeholder"] = "vas@email.sk"
        self.fields["messenger_type"].widget.attrs["class"] = base_classes
        self.fields["messenger_handle"].widget.attrs["class"] = base_classes
        self.fields["messenger_handle"].widget.attrs["placeholder"] = "@username alebo +421..."
        self.fields["message"].widget.attrs["class"] = f"{base_classes} resize-none"
        self.fields["consent"].widget.attrs["class"] = (
            "mt-0.5 h-4 w-4 rounded border border-zinc-300 text-zinc-900 focus:ring-zinc-900"
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.consent_given = self.cleaned_data.get("consent", False)
        if commit:
            instance.save()
        return instance
