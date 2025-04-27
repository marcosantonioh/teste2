from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Modulo(models.Model):
    
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    
    def __str__(self):
        return self.nome


class Secao(models.Model):
    
    # Definindo as opções de status
    STATUS_CHOICES = [
        ('completado', 'Completado'),
        ('livre', 'Livre'),
        ('bloqueado', 'Bloqueado'),
    ]
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='livre')
    modulo = models.ForeignKey(Modulo, related_name='secoes', on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    
    def __str__(self):
        return f"Seção {self.nome} no módulo {self.modulo.nome}"


class Estacao(models.Model):
    
    # Definindo as opções de status
    STATUS_CHOICES = [
        ('completado', 'Completado'),
        ('livre', 'Livre'),
        ('bloqueado', 'Bloqueado'),
    ]
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='livre')
    secao = models.ForeignKey(Secao, related_name='estacoes', on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    
    def __str__(self):
        return f"Estação {self.nome} na seção {self.secao.nome}"


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

    estacao = models.ForeignKey(Estacao, related_name='exercicios', on_delete=models.CASCADE, default=1)
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

