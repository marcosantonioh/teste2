from django.shortcuts import render
from apps.usuarios.models import Perfil
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

@login_required(login_url="login_usuario")
def ranking(request):
    try:
        perfil = Perfil.objects.get(user=request.user)
    except Perfil.DoesNotExist:
        perfil = Perfil.objects.create(user=request.user)
        
    perfis = Perfil.objects.all().order_by('-pontos')  # Ordena por pontos (decrescente)

    context = {
        'perfil': perfil,
        'perfis': perfis,   # Lista de todos os perfis
    }
    # Adicione a lógica para a view ranking aqui
    return render(request, 'ranking/ranking.html', context)