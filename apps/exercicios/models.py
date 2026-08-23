from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Modulo(models.Model):

    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    ordem = models.PositiveIntegerField(
        default=0,
        help_text="Define a ordem de exibição do módulo (menor número aparece primeiro).",
    )

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ["ordem", "id"]  # Ordena por 'ordem', depois por 'id' como desempate


class Secao(models.Model):
    modulo = models.ForeignKey(Modulo, related_name="secoes", on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    ordem = models.PositiveIntegerField(
        default=0,
        help_text="Define a ordem de exibição da seção dentro do módulo (menor número aparece primeiro).",
    )

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ["ordem", "id"]  # Ordena por 'ordem', depois por 'id' como desempate


class Estacao(models.Model):
    secao = models.ForeignKey(Secao, related_name="estacoes", on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    disponivel_para_visitantes = models.BooleanField(
        default=False,
        help_text="Libera esta estação somente na experiência de demonstração.",
    )
    # Se precisar de ordem para Estações também, adicione um campo 'ordem' aqui

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ["id"]  # Ou ['ordem', 'id'] se adicionar campo de ordem


# Create your models here.
class Exercicio(models.Model):

    STATUS_CHOICES = [
        ("livre", "Livre"),  # Pronto para ser resolvido ou pulado
        ("concluido", "Concluído"),  # Resolvido corretamente
    ]

    TIPO_CHOICES = [
        ("mcq", "Múltipla Escolha"),
        ("lacuna", "Lacuna"),
        ("info", "Informativo"),
        ("vf", "Verdadeiro ou Falso"),
    ]

    modulo = models.ForeignKey(
        Modulo, on_delete=models.CASCADE
    )  # A chave estrangeira para o modelo Modulo
    estacao = models.ForeignKey(
        Estacao, related_name="exercicios", on_delete=models.CASCADE, default=1
    )
    titulo = models.CharField(max_length=200, null=True, blank=True)
    enunciado = models.TextField(null=True, blank=True)
    codigo = models.TextField(null=True, blank=True)
    imagem = models.ImageField(
        upload_to="exercicios/imagens/",
        null=True,
        blank=True,
        help_text="Imagem para exercícios informativos.",
    )
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    xp = models.IntegerField(default=10)
    explicacao = models.TextField(null=True, blank=True)

    # Campos para múltipla escolha
    alternativa_1 = models.CharField(max_length=300, null=True, blank=True)
    alternativa_2 = models.CharField(max_length=300, null=True, blank=True)
    alternativa_3 = models.CharField(max_length=300, null=True, blank=True)
    alternativa_4 = models.CharField(max_length=300, null=True, blank=True)

    RESPOSTAS_CHOICES = [
        ("1", "Alternativa 1"),
        ("2", "Alternativa 2"),
        ("3", "Alternativa 3"),
        ("4", "Alternativa 4"),
    ]

    resposta_correta = models.CharField(
        max_length=1,
        choices=RESPOSTAS_CHOICES,
        null=True,
        blank=True,
        help_text="Relevante para exercícios de Múltipla Escolha.",
    )

    resposta_texto_codigo = models.TextField(
        null=True,
        blank=True,
        help_text="Resposta esperada para exercícios de preencher a lacuna.",
    )

    resposta_vf_correta = models.BooleanField(
        null=True,
        blank=True,
        help_text="Resposta correta para exercícios de Verdadeiro ou Falso (True para Verdadeiro, False para Falso).",
    )

    class Meta:
        ordering = ["id"]  # Ou outra ordem padrão desejada para exercícios

    def __str__(self):
        return self.titulo or "Exercício sem título"


class ExercicioUsuario(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercicio = models.ForeignKey(
        Exercicio, related_name="progresso_usuarios", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20, choices=Exercicio.STATUS_CHOICES, default="livre"
    )
    xp_concedido = models.BooleanField(
        default=False,
        help_text="Indica se o XP deste exercício já foi entregue ao usuário.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("usuario", "exercicio")
        verbose_name = "Progresso de Exercício"
        verbose_name_plural = "Progresso de Exercícios"

    def __str__(self):
        return f"{self.usuario.username} - {self.exercicio} ({self.status})"


class ReporteExercicio(models.Model):
    MOTIVO_CHOICES = [
        ("enunciado_incorreto", "Enunciado incorreto"),
        ("resposta_incorreta", "Resposta incorreta"),
        ("codigo_com_problema", "Código com problema"),
        ("outro", "Outro"),
    ]
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("resolvido", "Resolvido"),
    ]

    exercicio = models.ForeignKey(
        Exercicio, related_name="reportes", on_delete=models.CASCADE
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    motivo = models.CharField(max_length=30, choices=MOTIVO_CHOICES)
    criado_em = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente")

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Reporte de exercício"
        verbose_name_plural = "Reportes de exercícios"

    def __str__(self):
        return f"Exercício #{self.exercicio_id} — {self.get_motivo_display()}"
