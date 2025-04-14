from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('admin/', admin.site.urls),
    path('usuarios/', include("apps.usuarios.urls")),
    path("exercicios/", include("apps.exercicios.urls",)),
    path("desafios/", include("apps.desafios.urls",)),
    path("ranking/", include("apps.ranking.urls")),
    path("login/", include("apps.usuarios.urls")),
    path('etapa/<int:numero>/', views.etapa, name='etapa'),
    # path('', include('apps.usuarios.urls')),
]

   
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
