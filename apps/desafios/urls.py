from django.urls import path, include
from .views import desafios

app_name = "desafios"

urlpatterns = [
    path("", desafios, name="desafios"),
]