from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('admin/', admin.site.urls),
    path("login/", include("apps.usuarios.urls")),
    path("ranking/", include("apps.ranking.urls")),
    path('usuarios/', include("apps.usuarios.urls")),
    path("desafios/", include("apps.desafios.urls",)),
    path("exercicios/", include("apps.exercicios.urls",)),
    path('etapa/<int:numero>/', views.etapa, name='etapa'),
    path('adminpainel/', include('apps.painel_admin.urls')),
]

   
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
