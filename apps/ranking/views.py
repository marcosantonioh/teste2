from django.shortcuts import render
from apps.usuarios.models import Perfil, Amizade
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db.models import Q

def obter_amigos(user):
    
    amizades = Amizade.objects.filter(
        Q(remetente=user) | Q(destinatario=user),
        status='aceita'
    )
    amigos_ids = []

    for amizade in amizades:
        if amizade.remetente == user:
            amigos_ids.append(amizade.destinatario.id)
        else:
            amigos_ids.append(amizade.remetente.id)

    return User.objects.filter(id__in=amigos_ids)



# @login_required(login_url="login_usuario")@login_required(login_url="usuarios:login_usuario")
def ranking(request):
    
    perfil = None
    perfis_amigos = []

    usuario_logado = request.user.is_authenticated

    if usuario_logado:
        try:
            perfil = Perfil.objects.get(user=request.user)
        except ObjectDoesNotExist:
            perfil = Perfil.objects.create(user=request.user)

        amigos = obter_amigos(request.user)
        perfis_amigos = Perfil.objects.filter(user__in=amigos).order_by('-xp')

    
    perfis_globais = Perfil.objects.all().order_by('-xp')[:20]

    context = {
        'perfil': perfil,
        'perfis_globais': perfis_globais,
        'perfis_amigos': perfis_amigos,
        'usuario_logado': usuario_logado,
    }
    return render(request, 'ranking/ranking.html', context)
