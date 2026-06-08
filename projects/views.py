import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectForm
from .models import Project, Skill


def project_list(request):
    active_skill = request.GET.get("skill", "").strip()
    qs = Project.objects.select_related("owner").prefetch_related("participants", "skills")

    if active_skill:
        qs = qs.filter(skills__name__iexact=active_skill).distinct()

    all_skills = Skill.objects.filter(projects__isnull=False).distinct().order_by("name")
    active_skill_object = all_skills.filter(name__iexact=active_skill).first()

    paginator = Paginator(qs, 12)
    page_number = request.GET.get("page")
    projects = paginator.get_page(page_number)

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
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok"})


@login_required
@require_POST
def toggle_participate(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    user = request.user
    if user == project.owner:
        return JsonResponse(
            {"status": "error", "message": "Владелец не может участвовать в своём проекте"},
            status=400,
        )
    if project.status == Project.STATUS_CLOSED:
        return JsonResponse(
            {"status": "error", "message": "Нельзя присоединиться к завершённому проекту"},
            status=400,
        )

    if user in project.participants.all():
        project.participants.remove(user)
        participating = False
    else:
        project.participants.add(user)
        participating = True

    return JsonResponse({"status": "ok", "participant": participating})


@login_required
@require_POST
def skill_add(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    skill_id = data.get("skill_id")
    name = data.get("name", "").strip()

    if skill_id:
        skill = get_object_or_404(Skill, id=skill_id)
    elif name:
        if len(name) > Skill._meta.get_field("name").max_length:
            return JsonResponse({"error": "Название навыка слишком длинное"}, status=400)
        skill = Skill.objects.filter(name__iexact=name).first()
        if skill is None:
            try:
                skill = Skill.objects.create(name=name)
            except IntegrityError:
                skill = Skill.objects.get(name__iexact=name)
    else:
        return JsonResponse({"error": "Укажите навык"}, status=400)

    project.skills.add(skill)
    return JsonResponse({"id": skill.id, "name": skill.name})


@login_required
@require_POST
def skill_remove(request, project_id, skill_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    skill = get_object_or_404(Skill, id=skill_id)
    project.skills.remove(skill)
    return JsonResponse({"status": "ok"})


def skills_autocomplete(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)
    skills = Skill.objects.filter(name__icontains=q).values("id", "name").order_by("name")[:10]
    return JsonResponse(list(skills), safe=False)
