from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from apps.usuarios.models import Perfil
# Create your views here.

@login_required(login_url="login_usuario")
def desafios(request):
    
    try:
        perfil = Perfil.objects.get(user=request.user)
    except ObjectDoesNotExist:
        perfil = Perfil.objects.create(user=request.user)
    
    context = {
        'perfil': perfil
    }
    
    return render(request, "desafios/desafios.html", context)