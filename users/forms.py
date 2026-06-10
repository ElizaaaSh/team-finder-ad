import re
from urllib.parse import urlparse

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.core.exceptions import ValidationError

from .models import User


PHONE_RE = re.compile(r"^(8|\+7)\d{10}$")


def normalize_phone(phone: str) -> str:
    phone = (phone or "").strip().replace(" ", "").replace("-", "")
    if phone.startswith("8") and len(phone) == 11:
        return "+7" + phone[1:]
    return phone


def validate_github_url(url: str) -> str:
    if not url:
        return url
    host = urlparse(url).netloc.lower()
    if host != "github.com" and not host.endswith(".github.com"):
        raise ValidationError("Ссылка должна вести на GitHub.")
    return url


class RegisterForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password"]
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "email": "Имейл",
        }

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Имейл")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user_cache = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise ValidationError("Неверный имейл или пароль")
            if not self.user_cache.is_active:
                raise ValidationError("Аккаунт заблокирован")
        return cleaned_data

    def get_user(self):
        return self.user_cache


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "Ссылка на GitHub",
        }
        widgets = {
            "avatar": forms.FileInput(attrs={"accept": "image/*"}),
            "about": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone", ""))
        if phone and not PHONE_RE.match(phone):
            raise ValidationError("Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX.")
        if phone:
            duplicate = User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists()
            if duplicate:
                raise ValidationError("Пользователь с таким телефоном уже существует.")
        return phone

    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url", ""))


class PasswordChangeForm(DjangoPasswordChangeForm):
    pass
