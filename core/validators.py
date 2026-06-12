from urllib.parse import urlparse

from django.core.exceptions import ValidationError


def validate_github_url(url: str) -> str:
    if not url:
        return url

    host = urlparse(url).netloc.lower()
    if host != "github.com" and not host.endswith(".github.com"):
        raise ValidationError("Ссылка должна вести на GitHub.")
    return url
