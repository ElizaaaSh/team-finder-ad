import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.core.exceptions import ValidationError

from core.constants import PHONE_PATTERN
from core.forms import GitHubURLValidationMixin
from .models import User
from .services import normalize_phone

PHONE_RE = re.compile(PHONE_PATTERN)


class RegisterForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password"]

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


class EditProfileForm(GitHubURLValidationMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]
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


class PasswordChangeForm(DjangoPasswordChangeForm):
    pass
