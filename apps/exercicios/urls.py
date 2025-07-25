from django.urls import path
from . import views

app_name = "exercicios"

urlpatterns = [
    path("", views.modulos, name="modulos"),
    path("modulos/", views.modulos, name='modulos'),  # ou remova essa, se preferir
    path('resolver/<int:exercicio_id>/', views.resolver_exercicio, name='resolver_exercicio'),
    path('percurso/<int:modulo_id>/', views.percurso, name='percurso'),
    path('iniciar_estacao/<int:exercicio_id>/', views.iniciar_exercicios, name='iniciar_estacao'),
    path('estacao_concluida/<int:estacao_id>/', views.estacao_concluida_view, name='estacao_concluida'),
    path('api/exercicio/<int:exercicio_id>/', views.get_exercicio_data, name='api_get_exercicio_data'),

]
