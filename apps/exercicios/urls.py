from django.urls import path, include
from .views import main_view, lista_exercicios, submeter_exercicio, modulos

app_name = "exercicios"

urlpatterns = [
    path("", main_view, name="main"),
    path("modulos/", modulos, name='modulos'),
    path("exercicios/", lista_exercicios, name='lista_exercicios'),
    path("<int:exercicio_id>/", submeter_exercicio, name="submeter"),
]