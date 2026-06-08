from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from projects.models import Project


User = get_user_model()

OWNER_EMAIL = "owner@example.com"
OTHER_USER_EMAIL = "other@example.com"
NEW_USER_EMAIL = "new@example.com"
PASSWORD = "password"
STRONG_PASSWORD = "strong-password"
NEW_PASSWORD = "new-strong-password"
OWNER_NAME = "Иван"
OWNER_SURNAME = "Иванов"
OTHER_USER_NAME = "Мария"
OTHER_USER_SURNAME = "Петрова"
NEW_USER_NAME = "Новый"
NEW_USER_SURNAME = "Пользователь"
PROJECT_NAME = "Тестовый проект"
PROJECT_DESCRIPTION = "Описание проекта"
NEW_PROJECT_NAME = "Новый проект"
NEW_PROJECT_DESCRIPTION = "Описание"
NEW_PROFILE_NAME = "Новое имя"
NEW_PROFILE_DESCRIPTION = "Новое описание"
PHONE = "+79990000000"
GITHUB_URL = "https://github.com/example"
USERS_REGISTER_ROUTE = "users:register"
USERS_LOGIN_ROUTE = "users:login"
USERS_LOGOUT_ROUTE = "users:logout"
USERS_EDIT_PROFILE_ROUTE = "users:edit_profile"
USERS_CHANGE_PASSWORD_ROUTE = "users:change_password"
USERS_DETAIL_ROUTE = "users:detail"
USERS_LIST_ROUTE = "users:list"
PROJECTS_LIST_ROUTE = "projects:list"
PROJECTS_CREATE_ROUTE = "projects:create"
PROJECTS_DETAIL_ROUTE = "projects:detail"
PROJECTS_EDIT_ROUTE = "projects:edit"
NAME_FIELD = "name"
SURNAME_FIELD = "surname"
EMAIL_FIELD = "email"
PASSWORD_FIELD = "password"
DESCRIPTION_FIELD = "description"
GITHUB_URL_FIELD = "github_url"
STATUS_FIELD = "status"
ABOUT_FIELD = "about"
PHONE_FIELD = "phone"
OLD_PASSWORD_FIELD = "old_password"
NEW_PASSWORD_FIELD = "new_password"
CONFIRM_PASSWORD_FIELD = "confirm_password"
PROJECTS_CONTEXT_KEY = "projects"
PARTICIPANTS_CONTEXT_KEY = "participants"
AUTH_USER_SESSION_KEY = "_auth_user_id"
EMPTY_VALUE = ""
PAGINATION_PAGE_SIZE = 12
PAGINATED_PROJECT_NAME_TEMPLATE = "Проект {index}"
PAGINATED_USER_EMAIL_TEMPLATE = "user{index}@example.com"
PAGINATED_USER_NAME_TEMPLATE = "Имя {index}"


class CommonFunctionalityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email=OWNER_EMAIL,
            password=PASSWORD,
            name=OWNER_NAME,
            surname=OWNER_SURNAME,
        )
        self.other_user = User.objects.create_user(
            email=OTHER_USER_EMAIL,
            password=PASSWORD,
            name=OTHER_USER_NAME,
            surname=OTHER_USER_SURNAME,
        )
        self.project = Project.objects.create(
            name=PROJECT_NAME,
            description=PROJECT_DESCRIPTION,
            owner=self.owner,
        )

    def test_registration_redirects_to_login(self):
        response = self.client.post(
            reverse(USERS_REGISTER_ROUTE),
            {
                NAME_FIELD: NEW_USER_NAME,
                SURNAME_FIELD: NEW_USER_SURNAME,
                EMAIL_FIELD: NEW_USER_EMAIL,
                PASSWORD_FIELD: STRONG_PASSWORD,
            },
        )

        self.assertRedirects(response, reverse(USERS_LOGIN_ROUTE))
        self.assertTrue(User.objects.filter(email=NEW_USER_EMAIL).exists())

    def test_login_and_logout_work(self):
        response = self.client.post(
            reverse(USERS_LOGIN_ROUTE),
            {EMAIL_FIELD: self.owner.email, PASSWORD_FIELD: PASSWORD},
        )
        self.assertRedirects(response, reverse(PROJECTS_LIST_ROUTE))

        response = self.client.get(reverse(USERS_LOGOUT_ROUTE))
        self.assertRedirects(response, reverse(PROJECTS_LIST_ROUTE))
        self.assertNotIn(AUTH_USER_SESSION_KEY, self.client.session)

    def test_guest_cannot_create_project_or_edit_profile(self):
        create_response = self.client.get(reverse(PROJECTS_CREATE_ROUTE))
        profile_response = self.client.get(reverse(USERS_EDIT_PROFILE_ROUTE))

        create_login_url = (
            f"{reverse(USERS_LOGIN_ROUTE)}?next={reverse(PROJECTS_CREATE_ROUTE)}"
        )
        self.assertRedirects(create_response, create_login_url)
        self.assertRedirects(
            profile_response,
            f"{reverse(USERS_LOGIN_ROUTE)}?next={reverse(USERS_EDIT_PROFILE_ROUTE)}",
        )

    def test_user_can_create_project(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(PROJECTS_CREATE_ROUTE),
            {
                NAME_FIELD: NEW_PROJECT_NAME,
                DESCRIPTION_FIELD: NEW_PROJECT_DESCRIPTION,
                GITHUB_URL_FIELD: EMPTY_VALUE,
                STATUS_FIELD: Project.STATUS_OPEN,
            },
        )

        project = Project.objects.get(name=NEW_PROJECT_NAME)
        self.assertRedirects(response, reverse(PROJECTS_DETAIL_ROUTE, args=[project.id]))
        self.assertEqual(project.owner, self.owner)

    def test_only_owner_can_edit_project(self):
        self.client.force_login(self.other_user)

        response = self.client.get(reverse(PROJECTS_EDIT_ROUTE, args=[self.project.id]))

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_owner_can_edit_profile_and_change_password(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse(USERS_EDIT_PROFILE_ROUTE),
            {
                NAME_FIELD: NEW_PROFILE_NAME,
                SURNAME_FIELD: self.owner.surname,
                ABOUT_FIELD: NEW_PROFILE_DESCRIPTION,
                PHONE_FIELD: PHONE,
                GITHUB_URL_FIELD: GITHUB_URL,
            },
        )
        self.assertRedirects(response, reverse(USERS_DETAIL_ROUTE, args=[self.owner.id]))
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.name, NEW_PROFILE_NAME)

        response = self.client.post(
            reverse(USERS_CHANGE_PASSWORD_ROUTE),
            {
                OLD_PASSWORD_FIELD: PASSWORD,
                NEW_PASSWORD_FIELD: NEW_PASSWORD,
                CONFIRM_PASSWORD_FIELD: NEW_PASSWORD,
            },
        )
        self.assertRedirects(response, reverse(USERS_DETAIL_ROUTE, args=[self.owner.id]))
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password(NEW_PASSWORD))

    def test_lists_are_paginated_by_twelve(self):
        for index in range(PAGINATION_PAGE_SIZE):
            Project.objects.create(
                name=PAGINATED_PROJECT_NAME_TEMPLATE.format(index=index),
                owner=self.owner,
            )
            User.objects.create_user(
                email=PAGINATED_USER_EMAIL_TEMPLATE.format(index=index),
                password=PASSWORD,
                name=PAGINATED_USER_NAME_TEMPLATE.format(index=index),
                surname=NEW_USER_SURNAME,
            )

        project_response = self.client.get(reverse(PROJECTS_LIST_ROUTE))
        users_response = self.client.get(reverse(USERS_LIST_ROUTE))

        self.assertEqual(
            len(project_response.context[PROJECTS_CONTEXT_KEY]),
            PAGINATION_PAGE_SIZE,
        )
        self.assertEqual(
            len(users_response.context[PARTICIPANTS_CONTEXT_KEY]),
            PAGINATION_PAGE_SIZE,
        )
