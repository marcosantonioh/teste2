# apps/mecanicas_jogo/tasks.py
from celery import shared_task


@shared_task
def restaurar_uma_vida_task(perfil_id):
    from apps.usuarios.models import Perfil
    from apps.usuarios.services import restaurar_vidas_usuario

    perfil = Perfil.objects.select_related("user").filter(pk=perfil_id).first()
    if perfil:
        restaurar_vidas_usuario(perfil.user)
