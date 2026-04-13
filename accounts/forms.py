from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from .models import User


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Sifre",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Sifre Tekrar",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "Ad",
            "last_name": "Soyad",
            "email": "E-posta",
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Bu e-posta zaten kullaniliyor.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        email = cleaned_data.get("email")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Sifreler eslesmiyor.")

        if password1:
            validate_password(password1)

        if email and password1 and email.split("@")[0].lower() in password1.lower():
            self.add_error("password1", "Sifre e-posta bilgisine cok benzememeli.")

        return cleaned_data

    def _generate_unique_username(self, email: str) -> str:
        base = email.split("@")[0].replace(" ", "").lower()
        if not base:
            base = "user"
        candidate = base
        i = 1
        while User.objects.filter(username=candidate).exists():
            i += 1
            candidate = f"{base}{i}"
        return candidate

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self._generate_unique_username(user.email)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    login = forms.CharField(label="E-posta veya kullanici adi")
    password = forms.CharField(
        label="Sifre",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    remember_me = forms.BooleanField(label="Beni hatirla", required=False)

    error_messages = {
        "invalid_credentials": "Gecersiz giris bilgileri.",
        "inactive": "Bu hesap pasif durumda.",
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        login_value = cleaned_data.get("login", "").strip()
        password = cleaned_data.get("password")

        if not login_value or not password:
            return cleaned_data

        username = login_value
        if "@" in login_value:
            user = User.objects.filter(email__iexact=login_value).first()
            if user:
                username = user.username

        self.user_cache = authenticate(
            request=self.request,
            username=username,
            password=password,
        )
        if self.user_cache is None:
            raise forms.ValidationError(self.error_messages["invalid_credentials"])
        if not self.user_cache.is_active:
            raise forms.ValidationError(self.error_messages["inactive"])

        return cleaned_data

    def get_user(self):
        return self.user_cache


class AdminRequestForm(forms.Form):
    reason = forms.CharField(
        label=_("Gerekçe"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
    )
