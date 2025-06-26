from django.urls import path, re_path
from app.api import api
from app.views import login_view, logout_view
from app.consumers import AtivadoConsumer

# Rotas HTTP normais
urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path("api/", api.urls, name='api'),
]

# Rotas WebSocket
websocket_urlpatterns = [
    re_path(r'ws/ativados/$', AtivadoConsumer.as_asgi()),
]