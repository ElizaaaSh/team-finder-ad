from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.constants import PROJECTS_PER_PAGE, SKILL_NAME_MAX_LENGTH, SKILL_SUGGEST_LIMIT
from core.services import paginate_queryset
from .forms import ProjectForm
from .models import Project, Skill
from .services import can_manage_project, json_or_post_data


def root_redirect(request: HttpRequest):
    return redirect("projects:list")


def project_list(request: HttpRequest):
    active_skill = request.GET.get("skill", "").strip()
    projects = Project.objects.select_related("owner").prefetch_related("participants", "skills")

    if active_skill:
        projects = projects.filter(skills__name=active_skill)

    projects = projects.order_by("-created_at")
    page_obj, query_prefix = paginate_queryset(request, projects, PROJECTS_PER_PAGE)

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
    form = ProjectForm(request.POST or None)
    if form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        project.participants.add(request.user)
        return redirect("projects:detail", pk=project.pk)

    return render(request, "projects/create-project.html", {"form": form, "is_edit": False})


@login_required
def edit_project(request: HttpRequest, pk: int):
    project = get_object_or_404(Project, pk=pk)
    if not can_manage_project(request, project):
        return HttpResponseForbidden("Нет прав для редактирования проекта.")

    form = ProjectForm(request.POST or None, instance=project)
    if form.is_valid():
        project = form.save()
        return redirect("projects:detail", pk=project.pk)

    return render(request, "projects/create-project.html", {"form": form, "is_edit": True})


@login_required
@require_POST
def complete_project(request: HttpRequest, pk: int):
    project = get_object_or_404(Project, pk=pk)
    if not can_manage_project(request, project):
        return JsonResponse({"status": "forbidden"}, status=HTTPStatus.FORBIDDEN)
    if project.status == Project.STATUS_OPEN:
        project.status = Project.STATUS_CLOSED
        project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": project.status})


@login_required
@require_POST
def toggle_participate(request: HttpRequest, pk: int):
    project = get_object_or_404(Project, pk=pk)
    if request.user == project.owner:
        return JsonResponse({"status": "forbidden"}, status=HTTPStatus.FORBIDDEN)

    is_participant = project.participants.filter(pk=request.user.pk).exists()
    if is_participant:
        project.participants.remove(request.user)
    else:
        project.participants.add(request.user)

    return JsonResponse({"status": "ok", "participant": not is_participant})


def skills_suggest(request: HttpRequest):
    q = request.GET.get("q", "").strip()
    skills = Skill.objects.all()
    if q:
        skills = skills.filter(name__istartswith=q)
    data = list(skills.order_by("name").values("id", "name")[:SKILL_SUGGEST_LIMIT])
    return JsonResponse(data, safe=False)


@login_required
@require_POST
def add_project_skill(request: HttpRequest, pk: int):
    project = get_object_or_404(Project, pk=pk)
    if not can_manage_project(request, project):
        return JsonResponse({"status": "forbidden"}, status=HTTPStatus.FORBIDDEN)

    data = json_or_post_data(request)
    skill_id = data.get("skill_id")
    name = (data.get("name") or "").strip()

    created = False
    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
    elif name:
        skill, created = Skill.objects.get_or_create(name=name[:SKILL_NAME_MAX_LENGTH])
    else:
        return JsonResponse(
            {"error": "skill_id or name is required"},
            status=HTTPStatus.BAD_REQUEST,
        )

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
    if not can_manage_project(request, project):
        return JsonResponse({"status": "forbidden"}, status=HTTPStatus.FORBIDDEN)
    if not project.skills.filter(pk=skill.pk).exists():
        return JsonResponse({"status": "not_found"}, status=HTTPStatus.NOT_FOUND)
    project.skills.remove(skill)
    return JsonResponse({"status": "ok", "removed": True})
