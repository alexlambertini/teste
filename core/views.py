from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")  # Redireciona se já estiver logado

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("dashboard")  # Redireciona para a API após login
        else:
            return render(request, "login.html", {"error": "Usuário ou senha inválidos"})

    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard_view(request):
    return render(request, "dashboard.html")


def imprimir_view(request):
    return render(request, "imprimir_recibo.html")
