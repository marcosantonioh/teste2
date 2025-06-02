from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='bloqueado')
    secao = models.ForeignKey(Secao, related_name='estacoes', on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    
    def __str__(self):
        return self.nome


# Create your models here.
class Exercicio(models.Model):
    
    STATUS_CHOICES = [
        ('livre', 'Livre'),         # Pronto para ser resolvido ou pulado
        ('concluido', 'Concluído'), # Resolvido corretamente
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
    enunciado = models.TextField(null=True, blank=True)
    codigo = models.TextField(null=True, blank=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='livre')
    dificuldade = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    xp = models.IntegerField(default=10)
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

@receiver(post_save, sender=Estacao)
def atualizar_status_estacoes_adjacentes(sender, instance, created, **kwargs):
    """
    Signal para:
    1. Garantir que a primeira estação de uma seção seja 'livre' na criação.
    2. Liberar a próxima estação quando a atual for completada.
    """
    secao = instance.secao

    if created:
        # Lógica para a primeira estação da seção ser 'livre'
        # Considera a estação com o menor ID como a primeira.
        # Se houver um campo 'ordem', seria melhor usá-lo.
        primeira_estacao_na_secao = Estacao.objects.filter(secao=secao).order_by('id').first()
        if instance == primeira_estacao_na_secao and instance.status == 'bloqueado':
            # Usar update para evitar recursão do sinal se instance.save() fosse chamado
            Estacao.objects.filter(pk=instance.pk).update(status='livre')
            # Atualiza a instância localmente se necessário para o restante do código no mesmo request,
            # mas o update já salvou no DB.
            instance.status = 'livre' 

    if instance.status == 'completado':
        # Lógica para liberar a próxima estação na mesma seção
        proxima_estacao = Estacao.objects.filter(secao=secao, id__gt=instance.id).order_by('id').first()
        if proxima_estacao and proxima_estacao.status == 'bloqueado':
            # Usar update para evitar recursão do sinal
            Estacao.objects.filter(pk=proxima_estacao.pk).update(status='livre')
