from django.shortcuts import render
from apps.usuarios.models import Perfil, Amizade
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

def obter_amigos(user):
    amizades_enviadas = Amizade.objects.filter(remetente=user, status='aceita').values_list('destinatario', flat=True)
    amizades_recebidas = Amizade.objects.filter(destinatario=user, status='aceita').values_list('remetente', flat=True)
    return User.objects.filter(id__in=list(amizades_enviadas) + list(amizades_recebidas))



# @login_required(login_url="login_usuario")@login_required(login_url="usuarios:login_usuario")
def ranking(request):
    perfil = Perfil.objects.get(user=request.user)
    
    perfis_globais = Perfil.objects.all().order_by('-pontos')
    
    # Obtém amigos do usuário
    amigos = obter_amigos(request.user)
    perfis_amigos = Perfil.objects.filter(user__in=amigos).order_by('-pontos')

    context = {
        'perfil': perfil,
        'perfis_globais': perfis_globais,
        'perfis_amigos': perfis_amigos,
        'usuario_logado': True,
    }
    return render(request, 'ranking/ranking.html', context)
