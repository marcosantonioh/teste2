import os
from django.conf import settings
from .models import Divisao

def criar_divisoes_padrao():
    divisoes = [
        ('Bronze', 'bronze.svg'),
        ('Prata', 'prata.svg'),
        ('Ouro', 'ouro.svg'),
        ('Esmeralda', 'esmeralda.svg'),
        ('Rubi', 'rubi.svg'),
        ('Ametista', 'ametista.svg'),
        ('Diamante', 'diamante.svg'),
    ]

    for nome, caminho in divisoes:
        Divisao.objects.get_or_create(nome=nome, defaults={'imagem_static': caminho})
