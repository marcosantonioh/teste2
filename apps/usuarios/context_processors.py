from .models import Amizade


def notificacoes_amizade(request):
    """Disponibiliza a quantidade de solicitações pendentes no menu global."""
    if not request.user.is_authenticated:
        return {"solicitacoes_amizade_pendentes": 0}

    return {
        "solicitacoes_amizade_pendentes": Amizade.objects.filter(
            destinatario=request.user,
            status=Amizade.STATUS_PENDENTE,
        ).count()
    }
