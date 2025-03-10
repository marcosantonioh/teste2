from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.usuarios.models import Perfil

@login_required(login_url="login_usuario")
def main_view(request):
    perfil = Perfil.objects.get(user=request.user)
    context = {
        'perfil': perfil
    }
    return render( request, 'exercicios/main.html', context)


def lista_exercicios(request):
    return render(request, 'exercicios/lista_exercicios.html')



def ranking():
    
    return 