from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password


class AccountLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())


class AccountRegisterForm(forms.Form):
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())

    def clean_email(self):
        email = (self.cleaned_data["email"] or "").strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Používateľ s týmto emailom už existuje.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Heslá sa musia zhodovať.")
            return cleaned_data

        if password1:
            validate_password(password1)
        return cleaned_data
