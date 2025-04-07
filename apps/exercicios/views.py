from django.contrib.auth.decorators import login_required
from apps.usuarios.models import Perfil
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from .models import Exercicio, Submission
from .forms import SubmissaoForm
from django.contrib import messages


# @login_required(login_url="usuarios:login_usuario")
def main_view(request):
    perfil = None
    if request.user.is_authenticated:
        try:
            perfil = Perfil.objects.get(user=request.user)
        except ObjectDoesNotExist:
            perfil = Perfil.objects.create(user=request.user)

    # Caso o usuário não esteja logado e não tenha feito o onboarding, redireciona
    elif not request.session.get('onboarding_concluido'):
        return redirect('etapas_onboarding')  # ou qual for o nome da sua view inicial

    
    context = {
        'perfil': perfil
    }
    return render( request, 'exercicios/main.html', context)



@login_required(login_url="usuarios:login_usuario")
def modulos(request):
    try:
        perfil = Perfil.objects.get(user=request.user)
    except ObjectDoesNotExist:
        perfil = Perfil.objects.create(user=request.user)
    
    context = {
        'perfil': perfil,
        'modulos': ['While', 'Do-While', 'For']  # Definindo os módulos
    }
    return render(request, 'exercicios/modulos.html', context)

# views.py

def lista_exercicios(request, modulo):
    try:
        perfil = Perfil.objects.get(user=request.user)
    except ObjectDoesNotExist:
        perfil = Perfil.objects.create(user=request.user)

     # Filtra os exercícios com base no módulo selecionado
    exercicios = Exercicio.objects.filter(modulo=modulo).order_by('bloqueado')

    context = {
        'perfil': perfil,
        'modulo': modulo,
        'exercicios': exercicios
    }
    
    return render(request, 'exercicios/listar.html', context)



def submeter_exercicio(request, exercicio_id):
    exercicio = get_object_or_404(Exercicio, id=exercicio_id)

    if request.method == 'POST':
        codigo_usuario = request.POST.get('codigo')
        correta = codigo_usuario.strip() == exercicio.resposta_correta.strip()

        # Salva a submissão no banco
        Submission.objects.create(
            usuario=request.user,
            exercicio=exercicio,
            codigo_submetido=codigo_usuario,
            correta=correta
        )
        
        return render(request, 'exercicios/resultado.html', {'correta': correta, 'exercicio': exercicio})

    return render(request, 'exercicios/submeter.html', {'exercicio': exercicio})


