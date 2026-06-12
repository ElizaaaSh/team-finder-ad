import hashlib
import uuid
from io import BytesIO

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageDraw, ImageFont

from core.constants import (
    AVATAR_COLORS,
    AVATAR_DEFAULT_LETTER,
    AVATAR_FONT_PATHS,
    AVATAR_FONT_SIZE_RATIO,
    AVATAR_FORMAT,
    AVATAR_IMAGE_SIZE,
    AVATAR_SHADOW_COLOR,
    AVATAR_SHADOW_OFFSET,
    AVATAR_TEXT_ANCHOR,
    AVATAR_TEXT_COLOR,
    AVATAR_UPLOAD_DIR,
    USER_ABOUT_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_PHONE_MAX_LENGTH,
    USER_SURNAME_MAX_LENGTH,
)
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("Адрес электронной почты", unique=True)
    name = models.CharField("Имя", max_length=USER_NAME_MAX_LENGTH)
    surname = models.CharField("Фамилия", max_length=USER_SURNAME_MAX_LENGTH)
    avatar = models.ImageField("Аватар", upload_to=AVATAR_UPLOAD_DIR, blank=True)
    phone = models.CharField("Телефон", max_length=USER_PHONE_MAX_LENGTH, blank=True)
    github_url = models.URLField("Ссылка на GitHub", blank=True)
    about = models.TextField("О себе", max_length=USER_ABOUT_MAX_LENGTH, blank=True)
    is_active = models.BooleanField("Активный пользователь", default=True)
    is_staff = models.BooleanField("Администратор", default=False)
    date_joined = models.DateTimeField("Дата регистрации", auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        ordering = ["-date_joined", "-id"]
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
        bg_color = self._avatar_color()
        image = Image.new("RGB", (AVATAR_IMAGE_SIZE, AVATAR_IMAGE_SIZE), color=bg_color)
        draw = ImageDraw.Draw(image)
        letter = (self.name[:1] or self.email[:1] or AVATAR_DEFAULT_LETTER).upper()
        font = self._avatar_font()
        center = self._avatar_center()
        shadow_center = (center[0] + AVATAR_SHADOW_OFFSET, center[1] + AVATAR_SHADOW_OFFSET)

        draw.text(
            shadow_center,
            letter,
            fill=AVATAR_SHADOW_COLOR,
            font=font,
            anchor=AVATAR_TEXT_ANCHOR,
        )
        draw.text(
            center,
            letter,
            fill=AVATAR_TEXT_COLOR,
            font=font,
            anchor=AVATAR_TEXT_ANCHOR,
        )

        buffer = BytesIO()
        image.save(buffer, format=AVATAR_FORMAT)
        return ContentFile(buffer.getvalue())

    def _avatar_color(self) -> tuple[int, int, int]:
        key = self.email or self.name or AVATAR_DEFAULT_LETTER
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        color_index = int(digest[:8], 16) % len(AVATAR_COLORS)
        return AVATAR_COLORS[color_index]

    @staticmethod
    def _avatar_center() -> tuple[int, int]:
        coordinate = AVATAR_IMAGE_SIZE // 2
        return coordinate, coordinate

    @staticmethod
    def _avatar_font():
        font_size = int(AVATAR_IMAGE_SIZE * AVATAR_FONT_SIZE_RATIO)
        for font_path in AVATAR_FONT_PATHS:
            try:
                return ImageFont.truetype(font_path, font_size)
            except OSError:
                continue
        return ImageFont.load_default(size=font_size)
