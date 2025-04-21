from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.login_usuario, name="login_usuario"),
    path("logout/", views.logout_usuario, name="logout_usuario"),
    path("cadastro/", views.cadastrar_usuario, name="cadastro_usuario"),
    path("perfil/", views.perfil_view, name="perfil_usuario"),
    path("perfil/editar/", views.editar_perfil, name="editar_perfil"),
    path("perfil/editar/preferencias", views.preferencias, name="preferencias"),
    path("perfil/amigos/", views.amigos, name="amigos"),
    path("perfil/amigos/encontrar", views.encontrar_amigos, name="encontrar_amigos"),
    path("perfil/amigos/convidar", views.convidar_amigos, name="convidar_amigos"),

]