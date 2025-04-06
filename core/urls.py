from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('admin/', admin.site.urls),
    path('usuarios/', include("apps.usuarios.urls")),
    path("exercicios/", include("apps.exercicios.urls",)),
    path("desafios/", include("apps.desafios.urls",)),
    path("ranking/", include("apps.ranking.urls")),
    path("login/", include("apps.usuarios.urls")),
    path('teste/', views.acesso_sem_login, name='acesso_sem_login'),
    # path('', include('apps.usuarios.urls')),
]
