from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.login_usuario, name="login_usuario"),
    path("logout/", views.logout_usuario, name="logout_usuario"),
    path("cadastro/", views.cadastrar_usuario, name="cadastro_usuario"),
    path("perfil/", views.perfil_view, name="perfil_usuario"),
    path("perfil/amigos/", views.amigos, name="amigos"),
    path("perfil/editar/", views.editar_perfil, name="editar_perfil"),
    path("perfil/editar/preferencias", views.preferencias, name="preferencias"),
    path("perfil/amigos/encontrar", views.encontrar_amigos, name="encontrar_amigos"),
    path("perfil/amigos/convidar", views.convidar_amigos, name="convidar_amigos"),
    path("perfil/<str:username>/", views.ver_perfil_usuario, name="ver_perfil_usuario"),
    path('enviar-solicitacao/<int:destinatario_id>/', views.enviar_solicitacao_view, name='enviar_solicitacao'),
    path('solicitacoes/<int:amizade_id>/aceitar/', views.responder_solicitacao, {'resposta': 'aceitar'}, name='aceitar_solicitacao'),
    path('solicitacoes/<int:amizade_id>/recusar/', views.responder_solicitacao, {'resposta': 'recusar'}, name='recusar_solicitacao'),
    path('remover-amigo/<int:amigo_id>/', views.remover_amigo, name='remover_amigo'),
]
