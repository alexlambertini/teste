from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
#static configs
from django.conf import settings
from django.conf.urls.static import static
from core.views import login_view, logout_view, dashboard_view, imprimir_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('work/', include('app.urls')),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("", lambda request: redirect("login")),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("imprimir/", imprimir_view, name="imprimir"),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
