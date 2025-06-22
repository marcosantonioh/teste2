# apps/mecanicas_jogo/tasks.py
from celery import shared_task
from apps.usuarios.models import Perfil # Importe o modelo Perfil corretamente
from django.utils import timezone
from django.db import models

@shared_task
def verificar_e_restaurar_vidas():
    perfis = Perfil.objects.filter(vidas__lt=models.F('max_vidas')) # Apenas perfis que não têm o máximo de vidas

    for perfil in perfis:
        # Você pode passar o intervalo de restauração como argumento para o método ou defini-lo aqui
        if perfil.precisa_restaurar_vida(intervalo_restauracao_minutos=15): # Exemplo: 15 minutos
            perfil.restaurar_vida()
            # Opcional: logar a restauração de vida
            print(f"Vida restaurada para {perfil.user.username}. Vidas atuais: {perfil.vidas}")

# Você chamaria esta tarefa periodicamente, por exemplo, a cada 5 ou 10 minutos, via Celery Beat.