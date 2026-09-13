from apps.exercicios.models import ExercicioUsuario

from .models import Conquista, ConquistaUsuario


def sincronizar_conquistas(usuario):
    """Concede conquistas cujas metas já foram alcançadas pelo usuário."""
    exercicios_concluidos = ExercicioUsuario.objects.filter(
        usuario=usuario, status="concluido"
    ).count()

    conquistas_disponiveis = Conquista.objects.filter(
        tipo_requisito=Conquista.TIPO_REQUISITO_EXERCICIOS,
        meta__lte=exercicios_concluidos,
    )
    for conquista in conquistas_disponiveis:
        ConquistaUsuario.objects.get_or_create(usuario=usuario, conquista=conquista)
