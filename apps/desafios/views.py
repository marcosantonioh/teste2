from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from apps.usuarios.models import Perfil
from apps.desafios.models import DesafioUsuario

# Create your views here.

@login_required
def desafios(request):
    
    desafios_usuario = DesafioUsuario.objects.filter(usuario=request.user)
    
    for du in desafios_usuario:
        try:
            du.porcentagem = int((du.progresso / du.desafio.meta) * 100)
        except ZeroDivisionError:
            du.porcentagem = 0
    
    return render(request, 'apps/exercicios/modulos.html', {
        'desafios_usuario': desafios_usuario
    })

