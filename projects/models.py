from django.conf import settings
from django.db import models
from django.urls import reverse

from core.constants import (
    PROJECT_NAME_MAX_LENGTH,
    PROJECT_STATUS_MAX_LENGTH,
    SKILL_NAME_MAX_LENGTH,
)


class Skill(models.Model):
    name = models.CharField("Название навыка", max_length=SKILL_NAME_MAX_LENGTH, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Открыт"),
        (STATUS_CLOSED, "Закрыт"),
    ]

    name = models.CharField("Название проекта", max_length=PROJECT_NAME_MAX_LENGTH)
    description = models.TextField("Описание проекта", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Автор проекта",
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    github_url = models.URLField("Ссылка на GitHub", blank=True)
    status = models.CharField(
        "Статус проекта",
        max_length=PROJECT_STATUS_MAX_LENGTH,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Участники проекта",
        related_name="participated_projects",
        blank=True,
    )
    skills = models.ManyToManyField(
        Skill,
        verbose_name="Необходимые навыки",
        related_name="projects",
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("projects:detail", kwargs={"pk": self.pk})
