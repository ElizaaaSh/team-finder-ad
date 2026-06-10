from urllib.parse import urlparse

from django import forms
from django.core.exceptions import ValidationError

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        labels = {
            "name": "Название проекта",
            "description": "Описание проекта",
            "github_url": "Ссылка на GitHub",
            "status": "Статус",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
        }

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url", "")
        if not url:
            return url
        host = urlparse(url).netloc.lower()
        if host != "github.com" and not host.endswith(".github.com"):
            raise ValidationError("Ссылка должна вести на GitHub.")
        return url
