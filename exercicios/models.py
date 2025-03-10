from django.db import models

# Create your models here.
class Exercicio(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    tipo = models.CharField(max_length=50, choices=[('mcq', 'Múltipla Escolha'), ('code', 'Código')])
    dificuldade = models.IntegerField(default=1)
