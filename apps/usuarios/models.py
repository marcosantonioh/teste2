from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
import datetime
from apps.ranking.models import Divisao

class Perfil(models.Model):
    AVATARES = {
        "coruja-logica": {
            "nome": "Coruja Lógica",
            "arquivo": "img/avatares/comuns/Coruja Lógica.png",
            "raridade": "comum",
        },
        "guardiao-dos-vetores": {
            "nome": "Guardião dos Vetores",
            "arquivo": "img/avatares/lendarios/Guardião dos Vetores.png",
            "raridade": "lendario",
            "conquista": "guardiao-da-logica",
        },
        "explorador-azul": {
            "nome": "Explorador Azul",
            "arquivo": "img/avatares/comuns/Explorador Azul.png",
            "raridade": "comum",
        },
        "raposa-dev": {
            "nome": "Raposa Dev",
            "arquivo": "img/avatares/comuns/Raposa Dev.png",
            "raridade": "comum",
        },
        "hacker-neon": {
            "nome": "Hacker Neon",
            "arquivo": "img/avatares/raros/Hacker Neon.png",
            "raridade": "raro",
            "conquista": "mente-analitica",
        },
        "robo-aprendiz": {
            "nome": "Robô Aprendiz",
            "arquivo": "img/avatares/comuns/Robô Aprendiz.png",
            "raridade": "comum",
        },
        "explorador-verde": {
            "nome": "Explorador Verde",
            "arquivo": "img/avatares/comuns/Explorador Verde.png",
            "raridade": "comum",
        },
        "explorador-cyber": {
            "nome": "Explorador Cyber",
            "arquivo": "img/avatares/raros/Explorador Cyber.png",
            "raridade": "raro",
            "conquista": "primeiros-passos",
        },
        "robo-advanced": {
            "nome": "Robô Advanced",
            "arquivo": "img/avatares/raros/Robô Advanced.png",
            "raridade": "raro",
            "conquista": "construtor-avancado",
        },
        "lenda-do-percurso": {
            "nome": "Lenda do Percurso Lendário",
            "arquivo": "img/avatares/lendarios/Lenda do Percurso Lendario.png",
            "raridade": "lendario",
            "conquista": "lenda-do-percurso",
        },
        "mestre-dos-loops": {
            "nome": "Mestre dos Loops",
            "arquivo": "img/avatares/raros/Mestre dos Loops.png",
            "raridade": "raro",
            "conquista": "dominio-dos-loops",
        },
        "panda-code": {
            "nome": "Panda Code",
            "arquivo": "img/avatares/comuns/Panda Code.png",
            "raridade": "comum",
        },
    }
    AVATAR_CHOICES = [(chave, dados["nome"]) for chave, dados in AVATARES.items()]

    TEMPO_ESTUDO_CHOICES = [
        ('leve', 'Leve — 5 minutos'),
        ('regular', 'Regular — 10 minutos'),
        ('foco_total', 'Foco total — 20 minutos'),
    ]

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
    tempo_estudo = models.CharField(
        max_length=20,
        choices=TEMPO_ESTUDO_CHOICES,
        null=True,
        blank=True,
        help_text='Preferência de duração de estudo definida no onboarding.',
    )

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
    avatar = models.CharField(
        max_length=50,
        choices=AVATAR_CHOICES,
        default="coruja-logica",
        help_text="Avatar do catálogo selecionado pelo usuário.",
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

    @property
    def avatar_arquivo(self):
        """Caminho estático do avatar, com fallback para uma escolha válida."""
        return self.AVATARES.get(self.avatar, self.AVATARES["coruja-logica"])["arquivo"]

    def avatar_desbloqueado(self, codigo_avatar, conquistas_desbloqueadas=None):
        dados_avatar = self.AVATARES.get(codigo_avatar)
        if not dados_avatar:
            return False

        codigo_conquista = dados_avatar.get("conquista")
        if not codigo_conquista:
            return True
        if conquistas_desbloqueadas is not None:
            return codigo_conquista in conquistas_desbloqueadas
        return self.user.conquistas.filter(conquista__codigo=codigo_conquista).exists()
    
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


class Conquista(models.Model):
    TIPO_REQUISITO_EXERCICIOS = "exercicios_concluidos"
    TIPO_REQUISITO_CHOICES = [
        (TIPO_REQUISITO_EXERCICIOS, "Exercícios concluídos"),
    ]

    codigo = models.SlugField(unique=True)
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=255)
    tipo_requisito = models.CharField(max_length=30, choices=TIPO_REQUISITO_CHOICES)
    meta = models.PositiveIntegerField()

    class Meta:
        ordering = ["meta", "nome"]

    def __str__(self):
        return self.nome


class ConquistaUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conquistas")
    conquista = models.ForeignKey(Conquista, on_delete=models.CASCADE, related_name="usuarios")
    conquistada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "conquista")
        ordering = ["-conquistada_em"]

    def __str__(self):
        return f"{self.usuario.username} — {self.conquista.nome}"



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
