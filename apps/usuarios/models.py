from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pontos = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Pontuação")
    vidas = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    sequencia_dias = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    perfil_publico = models.BooleanField(default=False)
    bio = models.TextField(null=True, blank=True)
    seguidores = models.IntegerField(default=0)
    seguidos = models.IntegerField(default=0)
    data_inicio = models.DateTimeField(default=timezone.now)
    
    foto = models.ImageField(
        upload_to='fotos_perfil/',
        default='fotos_perfil/default.png',
        blank=True,
        null=True
    )

    GÊNEROS = (
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
    )

    genero = models.CharField(max_length=1, choices=GÊNEROS, null=True, blank=True)

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aceita', 'Aceita'),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')



    class Meta:
        db_table = 'perfil_usuario'  # Nome personalizado para a tabela

    def __str__(self):
        return self.user.username
    
    def tem_vidas(self):
        return self.vidas > 0

    
    
class Amizade(models.Model):
    remetente = models.ForeignKey(User, related_name='amizades_enviadas', on_delete=models.CASCADE)
    destinatario = models.ForeignKey(User, related_name='amizades_recebidas', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=[('pendente', 'Pendente'), ('aceita', 'Aceita'), ('recusada', 'Recusada')],
        default='pendente'
    )
    data_solicitacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('remetente', 'destinatario')

    def __str__(self):
        return f"{self.remetente} → {self.destinatario} ({self.status})"
