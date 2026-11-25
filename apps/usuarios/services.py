from apps.exercicios.models import ExercicioUsuario
from django.db import transaction
from django.utils import timezone

from .models import Conquista, ConquistaUsuario, Perfil


def restaurar_vidas_do_perfil(perfil, agora=None):
    """Restaura as vidas vencidas; deve receber um perfil bloqueado para escrita."""
    agora = agora or timezone.now()
    intervalo = perfil.intervalo_restauracao_por_vida
    if perfil.vidas_atuais >= perfil.max_vidas or intervalo.total_seconds() <= 0:
        return 0

    decorridos = agora - perfil.ultima_restauracao_vida
    quantidade = min(
        perfil.max_vidas - perfil.vidas_atuais,
        max(0, decorridos // intervalo),
    )
    if not quantidade:
        return 0

    perfil.vidas_atuais += quantidade
    perfil.ultima_restauracao_vida = (
        agora if perfil.vidas_atuais >= perfil.max_vidas
        else perfil.ultima_restauracao_vida + quantidade * intervalo
    )
    perfil.save(update_fields=["vidas_atuais", "ultima_restauracao_vida"])
    return quantidade


def restaurar_vidas_usuario(usuario, agora=None):
    """Aplica a recuperação sob bloqueio, inclusive após longos períodos offline."""
    if not usuario or not usuario.is_authenticated:
        return None
    with transaction.atomic():
        perfil = Perfil.objects.select_for_update().filter(user=usuario).first()
        if perfil:
            restaurar_vidas_do_perfil(perfil, agora=agora)
        return perfil


def sincronizar_conquistas(usuario):
    """Concede conquistas cujas metas já foram alcançadas pelo usuário."""
    exercicios_concluidos = ExercicioUsuario.objects.filter(
        usuario=usuario, status="concluido"
    ).count()

    conquistas_disponiveis = Conquista.objects.filter(
        tipo_requisito=Conquista.TIPO_REQUISITO_EXERCICIOS,
        meta__lte=exercicios_concluidos,
    )
    novas_conquistas = []
    for conquista in conquistas_disponiveis:
        _, criada = ConquistaUsuario.objects.get_or_create(
            usuario=usuario, conquista=conquista
        )
        if criada:
            novas_conquistas.append(conquista)
    return novas_conquistas
