from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from app import api
from app.models import Ativado
from .forms import LoginForm
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from ninja import NinjaAPI

api = NinjaAPI()


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # Redireciona para a página do app após login
            else:
                form.add_error(None, 'Usuário ou senha inválidos')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')  # Redireciona para a página de login após logout

@login_required  # Apenas usuários logados podem acessar essa página
def dashboard(request):
    return render(request, 'dashboard.html')  # Sua página principal ou protegida


def notificar_clientes():
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "ativados_group",
        {
            "type": "ativado.update",
            "data": {"action": "refresh", "message": "Dados atualizados"}
        }
    )

@api.delete("/ativados/{id}")
def deletar_ativado(request, id: int):
    ativado = Ativado.objects.get(id=id)
    ativado.delete()
    notificar_clientes()
    return {"success": True}
