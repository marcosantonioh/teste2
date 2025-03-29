from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from apps.usuarios import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include("apps.usuarios.urls")),
    path("exercicios/", include("apps.exercicios.urls",)),
    path("desafios/", include("apps.desafios.urls",)),
    path("ranking/", include("apps.ranking.urls")),
    path("", views.login_usuario , name="login_usuario" )
    # path('', include('apps.usuarios.urls')),
]
