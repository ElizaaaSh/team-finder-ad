from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.constants import USERS_PER_PAGE
from core.services import paginate_queryset
from .forms import EditProfileForm, LoginForm, PasswordChangeForm, RegisterForm
from .models import User


def register_view(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("users:login")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    form = LoginForm(request, request.POST or None)
    if form.is_valid():
        login(request, form.get_user())
        return redirect("projects:list")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def user_detail(request, pk: int):
    profile_user = get_object_or_404(
        User.objects.prefetch_related("owned_projects__participants"),
        pk=pk,
    )
    return render(request, "users/user-details.html", {"user": profile_user})


@login_required
def edit_profile(request):
    form = EditProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user,
    )
    if form.is_valid():
        form.save()
        return redirect("users:detail", pk=request.user.pk)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return redirect("users:detail", pk=request.user.pk)
    return render(request, "users/change_password.html", {"form": form})


def users_list(request):
    users = User.objects.filter(is_active=True).order_by("-date_joined", "-id")
    page_obj, query_prefix = paginate_queryset(request, users, USERS_PER_PAGE)

    context = {
        "participants": users,
        "page_obj": page_obj,
        "query_prefix": query_prefix,
    }
    return render(request, "users/participants.html", context)
