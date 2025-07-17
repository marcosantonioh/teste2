from django.db import models

class Divisao(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    imagem = models.CharField(max_length=200)

    def __str__(self):
        return self.nome
