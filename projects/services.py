import json

from django.http import HttpRequest

from .models import Project


def can_manage_project(request: HttpRequest, project: Project) -> bool:
    return request.user.is_authenticated and (
        request.user == project.owner or request.user.is_staff
    )


def json_or_post_data(request: HttpRequest) -> dict:
    if request.content_type == "application/json":
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST
