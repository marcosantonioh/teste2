from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
import datetime
from apps.ranking.models import Divisao

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    divisao = models.ForeignKey(Divisao, on_delete=models.SET_NULL, null=True, blank=True)
    xp = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Xp")
    sequencia_dias = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    bio = models.TextField(null=True, blank=True)
    seguidores = models.IntegerField(default=0)
    seguidos = models.IntegerField(default=0)
    data_inicio = models.DateTimeField(default=timezone.now)
    tema = models.CharField(max_length=20, default='claro')
    cristal = models.IntegerField(default=0)

    intervalo_restauracao_por_vida = models.DurationField(default=datetime.timedelta(minutes=15)) 
    vidas_atuais = models.IntegerField(default=5)
    max_vidas = models.IntegerField(default=5)
    ultima_restauracao_vida = models.DateTimeField(default=timezone.now)
    cooldown_ofensiva = models.DurationField(default=datetime.timedelta(hours=1))
    ultima_ofensiva_usada = models.DateTimeField(null=True, blank=True)

    
    visibilidade = models.CharField(
        max_length=10,
        choices=[('publico', 'Público'), ('privado', 'Privado')],
        default='publico'
    )

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


    class Meta:
        db_table = 'perfil_usuario'  # Nome personalizado para a tabela

    def __str__(self):
        return self.user.username
    
    def tem_vidas(self):
        return self.vidas_atuais > 0

    def pode_usar_ofensiva(self):
        if not self.ultima_ofensiva_usada:
            return True
        tempo_passado = timezone.now() - self.ultima_ofensiva_usada
        return tempo_passado >= self.cooldown_ofensiva

    def tempo_para_proxima_ofensiva(self):
        if self.pode_usar_ofensiva():
            return datetime.timedelta(seconds=0)
        tempo_restante = (self.ultima_ofensiva_usada + self.cooldown_ofensiva) - timezone.now()
        return max(tempo_restante, datetime.timedelta(seconds=0))

    @property
    def tempo_restante_para_proxima_vida(self):
        """
        Calcula o tempo restante para a próxima vida ser restaurada.
        Retorna um timedelta. Se as vidas estiverem cheias, retorna timedelta zero.
        """
        if self.vidas_atuais >= self.max_vidas:
            return datetime.timedelta(seconds=0)

        proxima_restauracao = self.ultima_restauracao_vida + self.intervalo_restauracao_por_vida
        tempo_restante = proxima_restauracao - timezone.now()
        
        # Garante que não retornamos um tempo negativo se a tarefa estiver atrasada
        return max(tempo_restante, datetime.timedelta(seconds=0))

    @property
    def posicao_no_ranking(self):
        ids_ordenados = Perfil.objects.order_by('-xp', '-sequencia_dias').values_list('user_id', flat=True)
        try:
            return list(ids_ordenados).index(self.user.id) + 1
        except ValueError:
            return None



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
