from django.urls import path, include
from .views import main_view, lista_exercicios, ranking

urlpatterns = [
    path("", main_view, name="main"),
    path("exercicios/", lista_exercicios, name='lista_exercicios'),
    path("ranking/", ranking, name='ranking'),

]