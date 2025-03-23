from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Exercicio(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    tipo = models.CharField(max_length=50, choices=[('mcq', 'Múltipla Escolha'), ('code', 'Código')])
    categoria = models.CharField(max_length=100)  # Ex: "Aula" ou "Quiz"
    dificuldade = models.IntegerField(default=1)
    xp = models.IntegerField(default=10)
    bloqueado = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'exercicio'
        
    def __str__(self):
        return self.titulo

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
