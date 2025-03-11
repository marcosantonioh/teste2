from django.contrib.auth.decorators import login_required
from apps.usuarios.models import Perfil
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from .models import Exercicio
from .forms import SubmissaoForm
from django.contrib import messages


@login_required(login_url="login_usuario")
def main_view(request):
    try:
        perfil = Perfil.objects.get(user=request.user)
    except ObjectDoesNotExist:
        perfil = Perfil.objects.create(user=request.user)
    
    context = {
        'perfil': perfil
    }
    return render( request, 'exercicios/main.html', context)


def lista_exercicios(request):
    try:
        perfil = Perfil.objects.get(user=request.user)
    except ObjectDoesNotExist:
        perfil = Perfil.objects.create(user=request.user)
    
    exercicios = Exercicio.objects.all()
    context = {
        'perfil': perfil,
        'exercicios': exercicios
    }
    return render(request, 'exercicios/listar.html', context)


def submeter_exercicio(request, exercicio_id):
    exercicio = get_object_or_404(Exercicio, id=exercicio_id)

    if request.method == "POST":
        form = SubmissaoForm(request.POST)
        if form.is_valid():
            resposta_usuario = form.cleaned_data["resposta"]
            
            if resposta_usuario.strip() == exercicio.resposta_correta.strip():
                messages.success(request, "Resposta correta! 🎉")
            else:
                messages.error(request, "Resposta incorreta. Tente novamente.")

            return redirect("exercicios:listar")

    else:
        form = SubmissaoForm()

    return render(request, "exercicios/submeter.html", {"exercicio": exercicio, "form": form})



def ranking(request):
    # Adicione a lógica para a view ranking aqui
    return render(request, 'exercicios/ranking.html')