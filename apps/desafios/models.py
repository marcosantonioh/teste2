from django.db import models
from django.contrib.auth.models import User

class Desafio(models.Model):
    titulo = models.CharField(max_length=100)
    meta = models.IntegerField(default=1)
    imagem = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    bau_imagem = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.titulo  # Corrigido de 'nome' para 'titulo'



class DesafioUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    desafio = models.ForeignKey('Desafio', on_delete=models.CASCADE)
    progresso = models.IntegerField(default=0)
    finalizado = models.BooleanField(default=False)
    data_finalizacao = models.DateTimeField(null=True, blank=True)

    def atualizar_progresso(self, valor):
        self.progresso += valor
        if self.progresso >= self.desafio.meta:
            self.finalizado = True
        self.save()

    def __str__(self):
        return f"{self.usuario.username} - {self.desafio.titulo}"
