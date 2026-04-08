import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import check_password
from django.shortcuts import redirect, render

# views.py


@login_required
@require_http_methods(["GET", "POST"])
def delete_account(request):
    if request.method == "POST":
        password = request.POST.get("password")

        if not password:
            return render(
                request,
                "accounts/delete_account.html",
                {"error": "Введите пароль."},
            )

        if not check_password(password, request.user.password):
            return render(
                request,
                "accounts/delete_account.html",
                {"error": "Неверный пароль."},
            )

        user = request.user
        logout(request)
        user.delete()
        return redirect("lists:public_lists")

    return render(request, "accounts/delete_account.html")


def login_page(request):
    return render(request, "accounts/login.html")


def login_ajax(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    username = request.POST.get("username")
    password = request.POST.get("password")

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"error": "Неверный логин или пароль"}, status=400)


def register_ajax(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    username = request.POST.get("username")
    email = request.POST.get("email")
    password = request.POST.get("password")

    # Проверка обязательных полей
    if not username or not email or not password:
        return JsonResponse({"error": "Все поля обязательны"}, status=400)

    # Проверка на существующего пользователя
    if User.objects.filter(username=username).exists():
        return JsonResponse(
            {"error": "Пользователь с таким именем уже существует"}, status=400
        )

    # Создаём пользователя
    User.objects.create_user(username=username, email=email, password=password)

    # Аутентификация, чтобы правильно определить backend
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"error": "Ошибка авторизации"}, status=400)


@require_POST
def logout_ajax(request):
    logout(request)
    return JsonResponse({"success": True})


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html")


@login_required
def set_theme(request):
    if request.method == "POST":
        data = json.loads(request.body)
        theme = data.get("theme", "light")
        request.user.theme = theme
        request.user.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)
