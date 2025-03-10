from django.db import models

# Create your models here.
class Usuario(models.Model):
    nome = models.CharField(max_length=100)  # Nome do usuário
    email = models.EmailField(unique=True)  # E-mail único
    pontuacao = models.IntegerField(default=0)  # Pontos acumulados

    def __str__(self):
        return self.nome  # Retorna o nome do usuário ao listar no Django Admin