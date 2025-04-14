from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pontos = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Pontuação")
    vidas = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    sequencia_dias = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    foto = models.ImageField(
        upload_to='fotos_perfil/',
        default='fotos_perfil/default.png',
        blank=True,
        null=True
    )


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
