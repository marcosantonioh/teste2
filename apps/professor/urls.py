from django.urls import path
from . import views

app_name = 'professor'

urlpatterns = [
    path('exercicios/', views.listar_exercicios, name='listar_exercicios'),
    path('exercicios/criar/<str:tipo_exercicio>/', views.criar_exercicio, name='criar_exercicio'),
    path('exercicios/editar/<int:id>/', views.editar_exercicio, name='editar_exercicio'),
    path('exercicios/deletar/<int:id>/', views.deletar_exercicio, name='deletar_exercicio'),
]
