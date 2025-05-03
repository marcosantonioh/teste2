from django.urls import path
from . import views

app_name = 'painel_admin'

urlpatterns = [
    path('exercicios/', views.lista_exercicios, name='lista_exercicios'),
    path('exercicios/novo/', views.novo_exercicio, name='novo_exercicio'),
    path('exercicios/editar/<int:id>/', views.editar_exercicio, name='editar_exercicio'),
    path('exercicios/deletar/<int:id>/', views.deletar_exercicio, name='deletar_exercicio'),
]
