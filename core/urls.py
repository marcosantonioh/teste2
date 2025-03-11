from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios', include("apps.usuarios.urls")),
    path("exercicios/", include("apps.exercicios.urls",)),
    path("exercicios/" , include("apps.exercicios.urls")),
    path('', include('apps.usuarios.urls')),
]
