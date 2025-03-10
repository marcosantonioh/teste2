from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios', include("usuarios.urls")),
    path("exercicios/" , include("exercicios.urls")),
    path('', include('usuarios.urls')),
]
