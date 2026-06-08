import json
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from team_finder.utils import paginate_queryset

from .forms import ProjectForm
from .models import Project, Skill

SKILLS_AUTOCOMPLETE_LIMIT = 10


def project_list(request):
    active_skill = request.GET.get("skill", "").strip()
    qs = Project.objects.select_related("owner").prefetch_related("participants", "skills")

    if active_skill:
        qs = qs.filter(skills__name__iexact=active_skill).distinct()

    all_skills = Skill.objects.filter(projects__isnull=False).distinct().order_by("name")
    active_skill_object = all_skills.filter(name__iexact=active_skill).first()

    projects = paginate_queryset(request, qs)

    return render(request, "projects/project_list.html", {
        "projects": projects,
        "all_skills": all_skills,
        "active_skill": active_skill_object.name if active_skill_object else active_skill,
    })


def project_detail(request, project_id):
    qs = Project.objects.select_related("owner").prefetch_related("participants", "skills")
    project = get_object_or_404(qs, id=project_id)
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            return redirect("projects:detail", project_id=project.id)
    else:
        form = ProjectForm()
    return render(request, "projects/create-project.html", {"form": form, "is_edit": False})


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("projects:detail", project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    return render(request, "projects/create-project.html", {"form": form, "is_edit": True})


@login_required
@require_POST
def complete_project(request, project_id):
    project = Project.objects.filter(id=project_id, owner=request.user).first()
    if project is None:
        return JsonResponse({"error": "Проект не найден"}, status=HTTPStatus.NOT_FOUND)

    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok"})


@login_required
@require_POST
def toggle_participate(request, project_id):
    project = Project.objects.filter(id=project_id).first()
    if project is None:
        return JsonResponse({"error": "Проект не найден"}, status=HTTPStatus.NOT_FOUND)

    user = request.user
    if user == project.owner:
        return JsonResponse(
            {"status": "error", "message": "Владелец не может участвовать в своём проекте"},
            status=HTTPStatus.BAD_REQUEST,
        )
    if project.status == Project.STATUS_CLOSED:
        return JsonResponse(
            {"status": "error", "message": "Нельзя присоединиться к завершённому проекту"},
            status=HTTPStatus.BAD_REQUEST,
        )

    is_participant = project.participants.filter(id=user.id).exists()
    if is_participant:
        project.participants.remove(user)
    else:
        project.participants.add(user)

    return JsonResponse({"status": "ok", "participant": not is_participant})


@login_required
@require_POST
def skill_add(request, project_id):
    project = Project.objects.filter(id=project_id, owner=request.user).first()
    if project is None:
        return JsonResponse({"error": "Проект не найден"}, status=HTTPStatus.NOT_FOUND)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=HTTPStatus.BAD_REQUEST)

    skill_id = data.get("skill_id")
    name = data.get("name", "").strip()

    if skill_id:
        skill = Skill.objects.filter(id=skill_id).first()
        if skill is None:
            return JsonResponse({"error": "Навык не найден"}, status=HTTPStatus.NOT_FOUND)
    elif name:
        if len(name) > Skill._meta.get_field("name").max_length:
            return JsonResponse(
                {"error": "Название навыка слишком длинное"},
                status=HTTPStatus.BAD_REQUEST,
            )
        skill, _ = Skill.objects.get_or_create(
            name__iexact=name,
            defaults={"name": name},
        )
    else:
        return JsonResponse({"error": "Укажите навык"}, status=HTTPStatus.BAD_REQUEST)

    project.skills.add(skill)
    return JsonResponse({"id": skill.id, "name": skill.name})


@login_required
@require_POST
def skill_remove(request, project_id, skill_id):
    project = Project.objects.filter(id=project_id, owner=request.user).first()
    if project is None:
        return JsonResponse({"error": "Проект не найден"}, status=HTTPStatus.NOT_FOUND)

    skill = Skill.objects.filter(id=skill_id).first()
    if skill is None:
        return JsonResponse({"error": "Навык не найден"}, status=HTTPStatus.NOT_FOUND)

    project.skills.remove(skill)
    return JsonResponse({"status": "ok"})


def skills_autocomplete(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse([], safe=False)
    skills = (
        Skill.objects.filter(name__icontains=query)
        .values("id", "name")
        .order_by("name")[:SKILLS_AUTOCOMPLETE_LIMIT]
    )
    return JsonResponse(list(skills), safe=False)
