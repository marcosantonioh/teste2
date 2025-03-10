from django.db import models
from django.contrib.auth.models import User

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pontos = models.IntegerField(default=0)
    vidas = models.IntegerField(default=5)
    sequencia_dias = models.IntegerField(default=0)

    class Meta:
        db_table = 'perfil_usuario'  # Nome personalizado para a tabela

    def __str__(self):
        return self.user.username