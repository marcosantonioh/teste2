from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.login_usuario, name="login_usuario"),
    path("logout/", views.logout_usuario, name="logout_usuario"),
    path("cadastro/", views.cadastrar_usuario, name="cadastro_usuario"),
    path("perfil/", views.perfil_view, name="perfil_usuario"),
]