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


class MissaoDiaria(models.Model):
    EXERCICIOS = 'exercicios'
    XP = 'xp'
    ESTACAO = 'estacao'
    TIPOS = [
        (EXERCICIOS, 'Conclua 3 exercícios'),
        (XP, 'Ganhe 20 XP'),
        (ESTACAO, 'Conclua 1 estação'),
    ]
    METAS = {EXERCICIOS: 3, XP: 20, ESTACAO: 1}
    IMAGENS = {
        EXERCICIOS: 'img/desafios/alvo.svg',
        XP: 'img/desafios/xp.svg',
        ESTACAO: 'img/desafios/alvo.svg',
    }

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='missoes_diarias')
    data = models.DateField()
    tipo = models.CharField(max_length=20, choices=TIPOS)
    progresso = models.PositiveIntegerField(default=0)
    concluida_em = models.DateTimeField(null=True, blank=True)
    cristais_recompensa = models.PositiveSmallIntegerField(default=5)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['usuario', 'data', 'tipo'], name='missao_diaria_unica')]
        ordering = ['id']

    @property
    def titulo(self):
        return dict(self.TIPOS)[self.tipo]

    @property
    def meta(self):
        return self.METAS[self.tipo]

    @property
    def porcentagem(self):
        return min(100, round(self.progresso * 100 / self.meta))

    @property
    def imagem(self):
        return self.IMAGENS[self.tipo]

    @property
    def bau_imagem(self):
        estado = 'open' if self.concluida_em else 'closed'
        return f'img/desafios/bau_madeira_{estado}.svg'

    def __str__(self):
        return f'{self.usuario} — {self.titulo} ({self.data})'
