import random
import uuid
from io import BytesIO

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageDraw, ImageFont


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("name", "Admin")
        extra_fields.setdefault("surname", "TeamFinder")
        extra_fields.setdefault("phone", "+79990000000")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("Адрес электронной почты", unique=True)
    name = models.CharField("Имя", max_length=124)
    surname = models.CharField("Фамилия", max_length=124)
    avatar = models.ImageField("Аватар", upload_to="avatars/", blank=True)
    phone = models.CharField("Телефон", max_length=12, blank=True)
    github_url = models.URLField("Ссылка на GitHub", blank=True)
    about = models.TextField("О себе", max_length=256, blank=True)
    is_active = models.BooleanField("Активный пользователь", default=True)
    is_staff = models.BooleanField("Администратор", default=False)
    date_joined = models.DateTimeField("Дата регистрации", auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        ordering = ["-id"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar.save(self._avatar_name(), self._generate_avatar(), save=False)
        super().save(*args, **kwargs)

    def _avatar_name(self) -> str:
        return f"avatar_{uuid.uuid4()}.png"

    def _generate_avatar(self) -> ContentFile:
        colors = [
            (37, 99, 235),    # blue
            (22, 163, 74),    # green
            (147, 51, 234),   # purple
            (220, 38, 38),    # red
            (234, 88, 12),    # orange
            (8, 145, 178),    # cyan
            (219, 39, 119),   # pink
        ]
        bg_color = random.choice(colors)
        image = Image.new("RGB", (256, 256), color=bg_color)
        draw = ImageDraw.Draw(image)
        letter = (self.name[:1] or self.email[:1] or "U").upper()
        font = self._avatar_font()

        # A small shadow keeps the letter readable even after the image is scaled
        # down to 24-50 px in project and participant cards.
        draw.text((132, 132), letter, fill=(0, 0, 0), font=font, anchor="mm")
        draw.text((128, 128), letter, fill=(255, 255, 255), font=font, anchor="mm")

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue())

    @staticmethod
    def _avatar_font():
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/local/share/fonts/DejaVuSans-Bold.ttf",
            "DejaVuSans-Bold.ttf",
        ]
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, 152)
            except OSError:
                continue
        return ImageFont.load_default(size=152)
