from django.urls import path
from . import views

app_name = "exercicios"

urlpatterns = [
    path("", views.modulos, name="modulos"),
    path("modulos/", views.modulos, name='modulos'),  # ou remova essa, se preferir
    path('resolver/<int:exercicio_id>/', views.resolver_exercicio, name='resolver_exercicio'),
    path('percurso/<int:modulo_id>/', views.percurso, name='percurso'),
    path('<str:modulo>/', views.lista_exercicios, name='lista_exercicios'),
]
