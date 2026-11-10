from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.desafios.services import missoes_do_dia


class Command(BaseCommand):
    help = 'Garante as três missões do dia sem apagar o progresso existente.'

    def handle(self, *args, **kwargs):
        quantidade = 0
        for usuario in get_user_model().objects.iterator():
            missoes_do_dia(usuario)
            quantidade += 1
        self.stdout.write(self.style.SUCCESS(f'Missões do dia verificadas para {quantidade} usuário(s).'))
