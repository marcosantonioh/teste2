from django.urls import path, include
from .views import main_view, lista_exercicios, submeter_exercicio, modulos

app_name = "exercicios"

urlpatterns = [
    path("", modulos, name="modulos"),
    path("modulos/", modulos, name='modulos'),
    path("<int:exercicio_id>/", submeter_exercicio, name="submeter"),
    path('exercicios/<str:modulo>/', lista_exercicios, name='lista_exercicios'),
]