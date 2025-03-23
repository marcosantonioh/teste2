from django.db import models
from django.contrib.auth.models import User
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

    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)
    dificuldade = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    xp = models.IntegerField(default=10)
    bloqueado = models.BooleanField(default=True)
    modulo = models.CharField(max_length=50, choices=MODULOS_CHOICES)

    class Meta:
        db_table = 'exercicio'
        
    def __str__(self):
        return f"{self.titulo} ({self.get_modulo_display()} - Dificuldade {self.dificuldade})"



class Submission(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    exercicio = models.ForeignKey(Exercicio, on_delete=models.CASCADE)
    codigo_submetido = models.TextField()
    correta = models.BooleanField(default=False)
    data_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'submissoes'

    def __str__(self):
        return f"{self.usuario.username} - {self.exercicio.titulo} - {'Correta' if self.correta else 'Errada'}"
