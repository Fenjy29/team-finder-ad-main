from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "name", "surname", "is_staff", "date_joined")
    search_fields = ("email", "name", "surname")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Личные данные", {
            "fields": ("name", "surname", "about", "phone", "github_url", "avatar"),
        }),
        ("Права", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "name", "surname", "password1", "password2"),
        }),
    )
    filter_horizontal = ("groups", "user_permissions")
