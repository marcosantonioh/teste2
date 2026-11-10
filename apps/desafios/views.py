from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from apps.usuarios.models import Perfil
from apps.desafios.services import missoes_do_dia
from datetime import datetime, time
from django.utils import timezone

@login_required
def desafios(request):
    desafios_usuario = missoes_do_dia(request.user)

    try:
        perfil = Perfil.objects.get(user=request.user)
    except Perfil.DoesNotExist:
        perfil = None

    # Cálculo de horas restantes até o fim do dia
    agora = timezone.now()
    if timezone.is_aware(agora):
        agora = timezone.localtime(agora)
    fim_do_dia = datetime.combine(agora.date(), time(23, 59, 59))
    if timezone.is_aware(agora):
        fim_do_dia = timezone.make_aware(fim_do_dia, timezone.get_current_timezone())
    tempo_restante = fim_do_dia - agora
    segundos_restantes = int(tempo_restante.total_seconds())
    horas_restantes = segundos_restantes // 3600

    return render(request, 'desafios/desafios.html', {
        'desafios_usuario': desafios_usuario,
        'perfil': perfil,
        'horas_restantes': int(horas_restantes),
    })

