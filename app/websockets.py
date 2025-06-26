from ninja import Router
from .consumers import AtivadoConsumer
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path

router = Router()

# Rotas WebSocket
websocket_urlpatterns = [
    re_path(r'ws/ativados/$', AtivadoConsumer.as_asgi()),
]

def get_websocket_application():
    return ProtocolTypeRouter({
        "websocket": URLRouter(websocket_urlpatterns),
    })