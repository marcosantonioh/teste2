from django.apps import AppConfig
import sys

class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.usuarios'

    def ready(self):
        """
        Executa código de inicialização quando o aplicativo está pronto.
        """
        # Verifica se estamos em modo DEBUG e se o comando é 'runserver'.
        # Isso evita que as sessões sejam limpas em produção ou ao rodar
        # outros comandos como 'migrate' ou 'shell'.
        is_runserver = any(arg == 'runserver' for arg in sys.argv)
        if is_runserver:
            from django.contrib.sessions.models import Session
            Session.objects.all().delete()
            print("✅ Sessões de usuário limpas no início do servidor.")