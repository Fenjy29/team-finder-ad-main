from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from projects.views import project_list


def home_redirect(request):
    return redirect("projects:list")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_redirect),
    path("project/list/", project_list),
    path("projects/", include("projects.urls")),
    path("users/", include("users.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
