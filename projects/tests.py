import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Project, Skill


User = get_user_model()


class ProjectVariantThreeTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="password",
            name="Owner",
            surname="User",
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="password",
            name="Member",
            surname="User",
        )
        self.project = Project.objects.create(name="Django project", owner=self.owner)
        self.skill = Skill.objects.create(name="Python")
        self.project.skills.add(self.skill)

    def test_project_list_filters_by_skill_case_insensitively(self):
        Project.objects.create(name="Other project", owner=self.member)

        response = self.client.get(reverse("projects:list"), {"skill": "python"})

        self.assertContains(response, self.project.name)
        self.assertNotContains(response, "Other project")
        self.assertEqual(response.context["active_skill"], "Python")

    def test_project_page_contains_required_skills(self):
        response = self.client.get(reverse("projects:detail", args=[self.project.id]))

        self.assertContains(response, "Необходимые навыки")
        self.assertContains(response, self.skill.name)

    def test_only_owner_can_add_and_remove_project_skill(self):
        add_url = reverse("projects:skill_add", args=[self.project.id])
        self.client.force_login(self.member)
        response = self.client.post(
            add_url,
            json.dumps({"name": "Django"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

        self.client.force_login(self.owner)
        response = self.client.post(
            add_url,
            json.dumps({"name": "Django"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        django_skill = Skill.objects.get(name="Django")
        self.assertTrue(self.project.skills.filter(id=django_skill.id).exists())

        response = self.client.post(
            reverse("projects:skill_remove", args=[self.project.id, django_skill.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.project.skills.filter(id=django_skill.id).exists())

    def test_existing_skill_is_reused_case_insensitively(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("projects:skill_add", args=[self.project.id]),
            json.dumps({"name": " python "}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Skill.objects.filter(name__iexact="python").count(), 1)

    def test_participants_are_visible_only_to_owner(self):
        self.project.participants.add(self.member)
        detail_url = reverse("projects:detail", args=[self.project.id])

        response = self.client.get(detail_url)
        self.assertNotContains(response, "Участники проекта")

        self.client.force_login(self.owner)
        response = self.client.get(detail_url)
        self.assertContains(response, "Участники проекта")

    def test_cannot_join_closed_project(self):
        self.project.status = Project.STATUS_CLOSED
        self.project.save(update_fields=["status"])
        self.client.force_login(self.member)

        response = self.client.post(
            reverse("projects:toggle_participate", args=[self.project.id])
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.project.participants.filter(id=self.member.id).exists())

    def test_technical_task_project_list_alias_works(self):
        response = self.client.get("/project/list/")

        self.assertEqual(response.status_code, 200)
