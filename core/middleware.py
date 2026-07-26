from django.utils.cache import add_never_cache_headers


class NaoArmazenarPaginasAutenticadasMiddleware:
    """Evita que dados privados reapareçam pelo cache do navegador após logout."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario_autenticado = request.user.is_authenticated
        response = self.get_response(request)

        if usuario_autenticado:
            add_never_cache_headers(response)

        return response
