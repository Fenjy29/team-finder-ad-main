from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ChangePasswordForm, EditProfileForm, LoginForm, RegistrationForm
from .models import User


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("users:login")
    else:
        form = RegistrationForm()
    return render(request, "users/register.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("projects:list")
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


def user_logout(request):
    logout(request)
    return redirect("projects:list")


def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, "users/user-details.html", {"user": user})


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("users:detail", user_id=request.user.id)
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["new_password"])
            request.user.save()
            login(request, request.user)
            return redirect("users:detail", user_id=request.user.id)
    else:
        form = ChangePasswordForm(request.user)
    return render(request, "users/change_password.html", {"form": form})


def users_list(request):
    qs = User.objects.all().order_by("-date_joined")
    paginator = Paginator(qs, 12)
    page_number = request.GET.get("page")
    participants = paginator.get_page(page_number)
    return render(request, "users/participants.html", {"participants": participants})
