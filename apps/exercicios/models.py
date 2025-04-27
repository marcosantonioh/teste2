from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# Create your models here.
class Exercicio(models.Model):
    
    MODULOS_CHOICES = [
        ('while','While'),
        ('do-while','Do-While'),
        ('for','For'),
    ]
    
    CATEGORIA_CHOICES = [
        ('aula', 'Aula'),
        ('quiz', 'Quiz'),
    ]

    TIPO_CHOICES = [
        ('mcq', 'Múltipla Escolha'),
        ('code', 'Código'),
    ]
    
    ORIGEM_CHOICES = [
        ('estatica', 'Estática'),
        ('ia', 'Gerada por IA'),
    ]


    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)
    dificuldade = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    xp = models.IntegerField(default=10)
    bloqueado = models.BooleanField(default=True)
    concluido = models.BooleanField(default=False)
    modulo = models.CharField(max_length=50, choices=MODULOS_CHOICES)
    origem = models.CharField(max_length=10, choices=ORIGEM_CHOICES, default='estatica')

    # Campos novos para múltipla escolha
    alternativas = models.JSONField(null=True, blank=True)  # {"A": "texto", "B": "texto"...}
    resposta_correta = models.CharField(max_length=255, null=True, blank=True)
    explicacao = models.TextField(null=True, blank=True)


    class Meta:
        db_table = 'exercicio'
        
    def __str__(self):
        return f"{self.titulo} ({self.get_modulo_display()} - Dificuldade {self.dificuldade})"

