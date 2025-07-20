from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from apps.usuarios.models import Perfil
from apps.desafios.models import DesafioUsuario
from datetime import datetime, time
import math

@login_required
def desafios(request):
    desafios_usuario = DesafioUsuario.objects.filter(usuario=request.user)

    for du in desafios_usuario:
        try:
            du.porcentagem = int((du.progresso / du.desafio.meta) * 100)
        except ZeroDivisionError:
            du.porcentagem = 0

    try:
        perfil = Perfil.objects.get(user=request.user)
    except Perfil.DoesNotExist:
        perfil = None

    # Cálculo de horas restantes até o fim do dia
    agora = datetime.now()
    fim_do_dia = datetime.combine(agora.date(), time(23, 59, 59))
    tempo_restante = fim_do_dia - agora
    segundos_restantes = int(tempo_restante.total_seconds())
    horas_restantes = segundos_restantes // 3600

    return render(request, 'desafios/desafios.html', {
        'desafios_usuario': desafios_usuario,
        'perfil': perfil,
        'horas_restantes': int(horas_restantes),
    })

