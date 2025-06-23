# apps/mecanicas_jogo/tasks.py
from celery import shared_task


@shared_task
def restaurar_uma_vida_task(perfil_id):
    # Esta funcionalidade foi desativada temporariamente.
    pass