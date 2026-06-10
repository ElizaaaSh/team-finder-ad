import json
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectForm
from .models import Project, Skill


def _can_manage_project(request: HttpRequest, project: Project) -> bool:
    return request.user.is_authenticated and (
        request.user == project.owner or request.user.is_staff
    )


def root_redirect(request: HttpRequest):
    return redirect("projects:list")


def project_list(request: HttpRequest):
    active_skill = request.GET.get("skill", "").strip()
    projects = Project.objects.select_related("owner").prefetch_related("participants", "skills")

    if active_skill:
        projects = projects.filter(skills__name=active_skill)

    projects = projects.order_by("-created_at")
    paginator = Paginator(projects, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    query_params.pop("page", None)
    query_prefix = urlencode(query_params)
    if query_prefix:
        query_prefix += "&"

    context = {
        "projects": projects,
        "page_obj": page_obj,
        "all_skills": Skill.objects.order_by("name").values_list("name", flat=True),
        "active_skill": active_skill,
        "query_prefix": query_prefix,
    }
    return render(request, "projects/project_list.html", context)


def project_detail(request: HttpRequest, pk: int):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants", "skills"),
        pk=pk,
    )
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def create_project(request: HttpRequest):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm()

    return render(request, "projects/create-project.html", {"form": form, "is_edit": False})


@login_required
def edit_project(request: HttpRequest, pk: int):
    project = get_object_or_404(Project, pk=pk)
    if not _can_manage_project(request, project):
        return HttpResponseForbidden("Нет прав для редактирования проекта.")

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    return render(request, "projects/create-project.html", {"form": form, "is_edit": True})


@login_required
@require_POST
def complete_project(request: HttpRequest, pk: int):
    project = get_object_or_404(Project, pk=pk)
    if not _can_manage_project(request, project):
        return JsonResponse({"status": "forbidden"}, status=403)
    if project.status == Project.STATUS_OPEN:
        project.status = Project.STATUS_CLOSED
        project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": project.status})


@login_required
@require_POST
def toggle_participate(request: HttpRequest, pk: int):
    project = get_object_or_404(Project, pk=pk)
    if request.user == project.owner:
        return JsonResponse({"status": "forbidden"}, status=403)

    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True

    return JsonResponse({"status": "ok", "participant": participant})


def skills_suggest(request: HttpRequest):
    q = request.GET.get("q", "").strip()
    skills = Skill.objects.all()
    if q:
        skills = skills.filter(name__istartswith=q)
    data = list(skills.order_by("name").values("id", "name")[:10])
    return JsonResponse(data, safe=False)


def _json_or_post_data(request: HttpRequest) -> dict:
    if request.content_type == "application/json":
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST


@login_required
@require_POST
def add_project_skill(request: HttpRequest, pk: int):
    project = get_object_or_404(Project, pk=pk)
    if not _can_manage_project(request, project):
        return JsonResponse({"status": "forbidden"}, status=403)

    data = _json_or_post_data(request)
    skill_id = data.get("skill_id")
    name = (data.get("name") or "").strip()

    created = False
    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
    elif name:
        skill, created = Skill.objects.get_or_create(name=name[:124])
    else:
        return JsonResponse({"error": "skill_id or name is required"}, status=400)

    already_added = project.skills.filter(pk=skill.pk).exists()
    if not already_added:
        project.skills.add(skill)

    return JsonResponse(
        {
            "id": skill.pk,
            "name": skill.name,
            "skill_id": skill.pk,
            "created": created,
            "added": not already_added,
        }
    )


@login_required
@require_POST
def remove_project_skill(request: HttpRequest, pk: int, skill_id: int):
    project = get_object_or_404(Project, pk=pk)
    skill = get_object_or_404(Skill, pk=skill_id)
    if not _can_manage_project(request, project):
        return JsonResponse({"status": "forbidden"}, status=403)
    if not project.skills.filter(pk=skill.pk).exists():
        return JsonResponse({"status": "not_found"}, status=404)
    project.skills.remove(skill)
    return JsonResponse({"status": "ok", "removed": True})
