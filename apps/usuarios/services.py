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
    novas_conquistas = []
    for conquista in conquistas_disponiveis:
        _, criada = ConquistaUsuario.objects.get_or_create(
            usuario=usuario, conquista=conquista
        )
        if criada:
            novas_conquistas.append(conquista)
    return novas_conquistas
