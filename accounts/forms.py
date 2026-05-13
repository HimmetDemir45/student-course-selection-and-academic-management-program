from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm as _DjangoPasswordChangeForm
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
    login = forms.CharField(
        label=_("E-posta veya kullanıcı adı"),
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-white/10 dark:bg-white/5 dark:text-white dark:focus:border-indigo-400 transition",
                "autocomplete": "username",
            },
        ),
    )
    password = forms.CharField(
        label=_("Şifre"),
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-white/10 dark:bg-white/5 dark:text-white dark:focus:border-indigo-400 transition",
                "autocomplete": "current-password",
            },
        ),
    )
    remember_me = forms.BooleanField(
        label=_("Beni hatırla"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-600 dark:border-white/10 dark:bg-white/5 dark:ring-offset-slate-900 transition"
            }
        ),
    )

    error_messages = {
        "invalid_credentials": _("Geçersiz giriş bilgileri."),
        "inactive": _("Bu hesap pasif durumda."),
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


class ProfileForm(forms.ModelForm):
    """Kullanıcının kendi adını, soyadını ve e-postasını düzenlemesi için form."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": _("Ad"),
            "last_name": _("Soyad"),
            "email": _("E-posta"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                field.widget.attrs.setdefault("class", "akd-input")

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        qs = User.objects.filter(email=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("Bu e-posta adresi başka bir hesap tarafından kullanılıyor."))
        return email


class AkdPasswordChangeForm(_DjangoPasswordChangeForm):
    """Django'nun PasswordChangeForm'u; etiketler Türkçeleştirilmiş."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = _("Mevcut şifre")
        self.fields["new_password1"].label = _("Yeni şifre")
        self.fields["new_password2"].label = _("Yeni şifre (tekrar)")
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "akd-input")


class AdminRequestForm(forms.Form):
    reason = forms.CharField(
        label=_("Gerekçe"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": "akd-input"}),
    )
