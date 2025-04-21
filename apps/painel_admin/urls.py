from django.urls import path
from . import views

app_name = 'painel_admin'

urlpatterns = [
    path('questoes/', views.lista_exercicios, name='lista_exercicios'),
    path('questoes/novo/', views.novo_exercicio, name='novo_exercicio'),
    path('questoes/editar/<int:id>/', views.editar_exercicio, name='editar_exercicio'),
    path('questoes/deletar/<int:id>/', views.deletar_exercicio, name='deletar_exercicio'),
]
