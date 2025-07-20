from django.core.management.base import BaseCommand
from desafios.models import Desafio, DesafioUsuario
from django.contrib.auth import get_user_model
import random

class Command(BaseCommand):
    help = 'Atualiza 3 desafios diários para cada usuário'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        usuarios = User.objects.all()
        desafios = list(Desafio.objects.all())

        for usuario in usuarios:
            # Remove desafios antigos do usuário
            DesafioUsuario.objects.filter(usuario=usuario).delete()

            # Escolhe 3 desafios aleatórios (ou os primeiros 3, mude como quiser)
            novos_desafios = random.sample(desafios, k=3) if len(desafios) >=3 else desafios

            # Cria as novas relações com progresso zerado
            for desafio in novos_desafios:
                DesafioUsuario.objects.create(
                    usuario=usuario,
                    desafio=desafio,
                    progresso=0,
                    finalizado=False
                )

        self.stdout.write(self.style.SUCCESS('Desafios diários atualizados com sucesso!'))
