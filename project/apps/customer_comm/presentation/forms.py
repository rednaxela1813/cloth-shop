from __future__ import annotations

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.customer_comm.constants import MessengerType
from apps.customer_comm.domain.dtos import SubmitInquiryInput


class PublicInquiryForm(forms.Form):
    name = forms.CharField(required=False, max_length=120, label=_("Meno"))
    email = forms.EmailField(label=_("E-mail"))
    phone = forms.CharField(required=False, max_length=40, label=_("Telefón"))
    messenger_type = forms.ChoiceField(choices=MessengerType.choices, label=_("Typ messengera"))
    messenger_handle = forms.CharField(required=False, max_length=120, label=_("Kontakt na messenger"))
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 6}), label=_("Správa"))
    consent = forms.BooleanField(
        required=True,
        label=_("Súhlasím so spracovaním osobných údajov za účelom odpovede na moju správu."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = (
            "mt-2 w-full rounded-xl border border-zinc-300 bg-white px-4 py-2 text-sm "
            "focus:outline-none focus:ring-2 focus:ring-zinc-900"
        )
        for name in ["name", "email", "phone", "messenger_type", "messenger_handle", "message"]:
            self.fields[name].widget.attrs["class"] = base_classes
        self.fields["message"].widget.attrs["class"] = f"{base_classes} resize-none"
        self.fields["name"].widget.attrs["placeholder"] = _("Zákazník Ricotti")
        self.fields["email"].widget.attrs["placeholder"] = "vas@email.sk"
        self.fields["phone"].widget.attrs["placeholder"] = "+421..."
        self.fields["messenger_handle"].widget.attrs["placeholder"] = "@username alebo +421..."
        self.fields["consent"].widget.attrs["class"] = (
            "mt-0.5 h-4 w-4 rounded border border-zinc-300 text-zinc-900 focus:ring-zinc-900"
        )

    def to_dto(self, *, consent_ip: str) -> SubmitInquiryInput:
        return SubmitInquiryInput(
            full_name=self.cleaned_data["name"],
            email=self.cleaned_data["email"],
            phone=self.cleaned_data["phone"],
            messenger_type=self.cleaned_data["messenger_type"],
            messenger_handle=self.cleaned_data["messenger_handle"],
            message=self.cleaned_data["message"],
            consent_given=self.cleaned_data["consent"],
            consent_ip=consent_ip,
            privacy_notice_version=settings.GDPR_PRIVACY_NOTICE_VERSION,
            consent_text_version=settings.GDPR_CONSENT_TEXT_VERSION,
        )
