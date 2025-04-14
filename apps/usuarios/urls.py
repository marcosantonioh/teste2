from django.urls import path
from .views import cadastrar_usuario, login_usuario, logout_usuario
from django.conf import settings
from django.conf.urls.static import static



app_name = "usuarios"

urlpatterns = [
    path("", login_usuario, name="login_usuario"),
    path("logout/", logout_usuario, name="logout_usuario"),
    path("cadastro/", cadastrar_usuario, name="cadastro_usuario"),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)