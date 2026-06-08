import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Project, Skill


User = get_user_model()

OWNER_EMAIL = "owner@example.com"
MEMBER_EMAIL = "member@example.com"
PASSWORD = "password"
OWNER_NAME = "Owner"
MEMBER_NAME = "Member"
USER_SURNAME = "User"
PROJECT_NAME = "Django project"
OTHER_PROJECT_NAME = "Other project"
PYTHON_SKILL_NAME = "Python"
PYTHON_SKILL_QUERY = "python"
PADDED_PYTHON_SKILL_QUERY = " python "
DJANGO_SKILL_NAME = "Django"
PROJECT_LIST_ROUTE = "projects:list"
PROJECT_DETAIL_ROUTE = "projects:detail"
SKILL_ADD_ROUTE = "projects:skill_add"
SKILL_REMOVE_ROUTE = "projects:skill_remove"
TOGGLE_PARTICIPATE_ROUTE = "projects:toggle_participate"
SKILL_QUERY_PARAMETER = "skill"
ACTIVE_SKILL_CONTEXT_KEY = "active_skill"
NAME_FIELD = "name"
STATUS_FIELD = "status"
JSON_CONTENT_TYPE = "application/json"
REQUIRED_SKILLS_TEXT = "Необходимые навыки"
PROJECT_PARTICIPANTS_TEXT = "Участники проекта"
PROJECT_LIST_ALIAS = "/project/list/"


class ProjectVariantThreeTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email=OWNER_EMAIL,
            password=PASSWORD,
            name=OWNER_NAME,
            surname=USER_SURNAME,
        )
        self.member = User.objects.create_user(
            email=MEMBER_EMAIL,
            password=PASSWORD,
            name=MEMBER_NAME,
            surname=USER_SURNAME,
        )
        self.project = Project.objects.create(name=PROJECT_NAME, owner=self.owner)
        self.skill = Skill.objects.create(name=PYTHON_SKILL_NAME)
        self.project.skills.add(self.skill)

    def test_project_list_filters_by_skill_case_insensitively(self):
        Project.objects.create(name=OTHER_PROJECT_NAME, owner=self.member)

        response = self.client.get(
            reverse(PROJECT_LIST_ROUTE),
            {SKILL_QUERY_PARAMETER: PYTHON_SKILL_QUERY},
        )

        self.assertContains(response, self.project.name)
        self.assertNotContains(response, OTHER_PROJECT_NAME)
        self.assertEqual(response.context[ACTIVE_SKILL_CONTEXT_KEY], PYTHON_SKILL_NAME)

    def test_project_page_contains_required_skills(self):
        response = self.client.get(reverse(PROJECT_DETAIL_ROUTE, args=[self.project.id]))

        self.assertContains(response, REQUIRED_SKILLS_TEXT)
        self.assertContains(response, self.skill.name)

    def test_only_owner_can_add_and_remove_project_skill(self):
        add_url = reverse(SKILL_ADD_ROUTE, args=[self.project.id])
        self.client.force_login(self.member)
        response = self.client.post(
            add_url,
            json.dumps({NAME_FIELD: DJANGO_SKILL_NAME}),
            content_type=JSON_CONTENT_TYPE,
        )
        self.assertEqual(response.status_code, 404)

        self.client.force_login(self.owner)
        response = self.client.post(
            add_url,
            json.dumps({NAME_FIELD: DJANGO_SKILL_NAME}),
            content_type=JSON_CONTENT_TYPE,
        )
        self.assertEqual(response.status_code, 200)
        django_skill = Skill.objects.get(name=DJANGO_SKILL_NAME)
        self.assertTrue(self.project.skills.filter(id=django_skill.id).exists())

        response = self.client.post(
            reverse(SKILL_REMOVE_ROUTE, args=[self.project.id, django_skill.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.project.skills.filter(id=django_skill.id).exists())

    def test_existing_skill_is_reused_case_insensitively(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(SKILL_ADD_ROUTE, args=[self.project.id]),
            json.dumps({NAME_FIELD: PADDED_PYTHON_SKILL_QUERY}),
            content_type=JSON_CONTENT_TYPE,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Skill.objects.filter(name__iexact=PYTHON_SKILL_QUERY).count(),
            1,
        )

    def test_participants_are_visible_only_to_owner(self):
        self.project.participants.add(self.member)
        detail_url = reverse(PROJECT_DETAIL_ROUTE, args=[self.project.id])

        response = self.client.get(detail_url)
        self.assertNotContains(response, PROJECT_PARTICIPANTS_TEXT)

        self.client.force_login(self.owner)
        response = self.client.get(detail_url)
        self.assertContains(response, PROJECT_PARTICIPANTS_TEXT)

    def test_cannot_join_closed_project(self):
        self.project.status = Project.STATUS_CLOSED
        self.project.save(update_fields=[STATUS_FIELD])
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(TOGGLE_PARTICIPATE_ROUTE, args=[self.project.id])
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.project.participants.filter(id=self.member.id).exists())

    def test_technical_task_project_list_alias_works(self):
        response = self.client.get(PROJECT_LIST_ALIAS)

        self.assertEqual(response.status_code, 200)
