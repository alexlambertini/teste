import os
from django.core.asgi import get_asgi_application
from app.websockets import get_websocket_application
from channels.routing import ProtocolTypeRouter


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": get_websocket_application(),
})