from django.shortcuts import render, get_object_or_404, redirect
from apps.exercicios.models import Exercicio
from .forms import ExercicioForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

@staff_member_required
def lista_exercicios(request):
    exercicios = Exercicio.objects.filter(origem='estatica')
    return render(request, 'painel_admin/lista.html', {'exercicios': exercicios})

@staff_member_required
def novo_exercicio(request):
    if request.method == 'POST':
        form = ExercicioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_exercicios')
    else:
        form = ExercicioForm()
    return render(request, 'painel_admin/form.html', {'form': form})

@staff_member_required
def editar_exercicio(request, id):
    exercicio = get_object_or_404(Exercicio, pk=id)
    if request.method == 'POST':
        form = ExercicioForm(request.POST, instance=exercicio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exercício atualizado com sucesso!')
            return redirect('lista_exercicios')
    else:
        form = ExercicioForm(instance=exercicio)
    return render(request, 'painel_admin/editar_exercicio.html', {'form': form, 'exercicio': exercicio})


@staff_member_required
def deletar_exercicio(request, id):
    exercicio = get_object_or_404(Exercicio, pk=id)
    exercicio.delete()
    messages.success(request, 'Exercício excluído com sucesso!')
    return redirect('lista_exercicios')
