from django.shortcuts import render
from apps.usuarios.models import Perfil

def ranking(request):
    # Ordena os perfis pelos pontos (do maior para o menor)

    perfis = Perfil.objects.all().order_by('-pontos') #top 10
    context = {
        'perfis': perfis
    }
    
    return render(request, 'ranking/ranking.html', context)
