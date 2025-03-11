from django.urls import path, include
from .views import main_view, lista_exercicios, ranking, submeter_exercicio

app_name = "exercicios"

urlpatterns = [
    path("", main_view, name="main"),
    path("exercicios/", lista_exercicios, name='lista_exercicios'),
    path("<int:exercicio_id>/", submeter_exercicio, name="submeter"),
    path("ranking/", ranking, name='ranking'),
]