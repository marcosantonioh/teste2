from django.apps import AppConfig


class RankingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ranking'

    def ready(self):
        from .utils import criar_divisoes_padrao
        criar_divisoes_padrao()