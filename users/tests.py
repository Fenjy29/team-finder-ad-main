from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from projects.models import Project


User = get_user_model()


class CommonFunctionalityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="password",
            name="Иван",
            surname="Иванов",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password",
            name="Мария",
            surname="Петрова",
        )
        self.project = Project.objects.create(
            name="Тестовый проект",
            description="Описание проекта",
            owner=self.owner,
        )

    def test_registration_redirects_to_login(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Новый",
                "surname": "Пользователь",
                "email": "new@example.com",
                "password": "strong-password",
            },
        )

        self.assertRedirects(response, reverse("users:login"))
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_login_and_logout_work(self):
        response = self.client.post(
            reverse("users:login"),
            {"email": self.owner.email, "password": "password"},
        )
        self.assertRedirects(response, reverse("projects:list"))

        response = self.client.get(reverse("users:logout"))
        self.assertRedirects(response, reverse("projects:list"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_guest_cannot_create_project_or_edit_profile(self):
        create_response = self.client.get(reverse("projects:create"))
        profile_response = self.client.get(reverse("users:edit_profile"))

        create_login_url = f"{reverse('users:login')}?next={reverse('projects:create')}"
        self.assertRedirects(create_response, create_login_url)
        self.assertRedirects(
            profile_response,
            f"{reverse('users:login')}?next={reverse('users:edit_profile')}",
        )

    def test_user_can_create_project(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("projects:create"),
            {
                "name": "Новый проект",
                "description": "Описание",
                "github_url": "",
                "status": Project.STATUS_OPEN,
            },
        )

        project = Project.objects.get(name="Новый проект")
        self.assertRedirects(response, reverse("projects:detail", args=[project.id]))
        self.assertEqual(project.owner, self.owner)

    def test_only_owner_can_edit_project(self):
        self.client.force_login(self.other_user)

        response = self.client.get(reverse("projects:edit", args=[self.project.id]))

        self.assertEqual(response.status_code, 404)

    def test_owner_can_edit_profile_and_change_password(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("users:edit_profile"),
            {
                "name": "Новое имя",
                "surname": self.owner.surname,
                "about": "Новое описание",
                "phone": "+79990000000",
                "github_url": "https://github.com/example",
            },
        )
        self.assertRedirects(response, reverse("users:detail", args=[self.owner.id]))
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.name, "Новое имя")

        response = self.client.post(
            reverse("users:change_password"),
            {
                "old_password": "password",
                "new_password": "new-strong-password",
                "confirm_password": "new-strong-password",
            },
        )
        self.assertRedirects(response, reverse("users:detail", args=[self.owner.id]))
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password("new-strong-password"))

    def test_lists_are_paginated_by_twelve(self):
        for index in range(12):
            Project.objects.create(name=f"Проект {index}", owner=self.owner)
            User.objects.create_user(
                email=f"user{index}@example.com",
                password="password",
                name=f"Имя {index}",
                surname="Пользователь",
            )

        project_response = self.client.get(reverse("projects:list"))
        users_response = self.client.get(reverse("users:list"))

        self.assertEqual(len(project_response.context["projects"]), 12)
        self.assertEqual(len(users_response.context["participants"]), 12)
