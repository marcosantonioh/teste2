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
        return self.nome


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
        return self.nome


# Create your models here.
class Exercicio(models.Model):
    
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
    enunciado = models.TextField(null=True, blank=True)
    codigo = models.TextField(null=True, blank=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)
    dificuldade = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    xp = models.IntegerField(default=10)
    bloqueado = models.BooleanField(default=True)
    concluido = models.BooleanField(default=False)
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE)  # A chave estrangeira para o modelo Modulo
    origem = models.CharField(max_length=10, choices=ORIGEM_CHOICES, default='estatica')

    # Campos novos para múltipla escolha

    alternativa_1 = models.CharField(max_length=300,null=True, blank=True)
    alternativa_2 = models.CharField(max_length=300,null=True, blank=True)
    alternativa_3 = models.CharField(max_length=300,null=True, blank=True)
    alternativa_4 = models.CharField(max_length=300,null=True, blank=True)

    RESPOSTAS_CHOICES = [
        ('1', 'Alternativa 1'),
        ('2', 'Alternativa 2'),
        ('3', 'Alternativa 3'),
        ('4', 'Alternativa 4'),
    ]

    resposta_correta = models.CharField(max_length=1, choices=RESPOSTAS_CHOICES)

    explicacao = models.TextField(null=True, blank=True)


    class Meta:
        db_table = 'exercicio'
        
    def __str__(self):
        return self.titulo
