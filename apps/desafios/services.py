"""Missões diárias geradas e atualizadas a partir de eventos reais de estudo."""
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.desafios.models import MissaoDiaria
from apps.usuarios.models import Perfil


def data_atual_missoes():
    agora = timezone.now()
    return timezone.localtime(agora).date() if timezone.is_aware(agora) else agora.date()


def missoes_do_dia(usuario):
    hoje = data_atual_missoes()
    for tipo, _ in MissaoDiaria.TIPOS:
        MissaoDiaria.objects.get_or_create(usuario=usuario, data=hoje, tipo=tipo)
    return list(MissaoDiaria.objects.filter(usuario=usuario, data=hoje).order_by('id'))


def registrar_exercicio_concluido(usuario, xp_ganho, estacao_concluida=False):
    """Conta apenas conclusões novas; entrega os cristais uma vez por missão."""
    if not usuario or not usuario.is_authenticated:
        return
    with transaction.atomic():
        missoes_do_dia(usuario)
        incrementos = {
            MissaoDiaria.EXERCICIOS: 1,
            MissaoDiaria.XP: max(0, xp_ganho),
            MissaoDiaria.ESTACAO: int(estacao_concluida),
        }
        for missao in MissaoDiaria.objects.select_for_update().filter(
            usuario=usuario, data=data_atual_missoes(), concluida_em__isnull=True
        ):
            incremento = incrementos[missao.tipo]
            if not incremento:
                continue
            missao.progresso = min(missao.meta, missao.progresso + incremento)
            if missao.progresso == missao.meta:
                missao.concluida_em = timezone.now()
                Perfil.objects.filter(user=usuario).update(
                    cristal=F('cristal') + missao.cristais_recompensa
                )
            missao.save(update_fields=['progresso', 'concluida_em'])
