import os
from django.conf import settings
from .models import Divisao

def criar_divisoes_padrao():
    divisoes = [
        ('Bronze', 'img/ranking/bronze.svg'),
        ('Prata', 'img/ranking/prata.svg'),
        ('Ouro', 'img/ranking/ouro.svg'),
        ('Esmeralda', 'img/ranking/esmeralda.svg'),
        ('Rubi', 'img/ranking/rubi.svg'),
        ('Ametista', 'img/ranking/ametista.svg'),
        ('Diamante', 'img/ranking/diamante.svg'),
    ]

    for nome, caminho in divisoes:
        Divisao.objects.get_or_create(nome=nome, defaults={'imagem': caminho})