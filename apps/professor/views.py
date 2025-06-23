from django.shortcuts import render, get_object_or_404, redirect
from apps.exercicios.models import Exercicio
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import Http404
from apps.exercicios.forms import (
    ExercicioMultiplaEscolhaForm,
    ExercicioCodigoForm, 
    ExercicioLacunaForm,
    ExercicioVerdadeiroFalsoForm,
)

# Função auxiliar para obter a classe de formulário correta baseada no tipo de exercício
def get_exercicio_form_class(tipo_exercicio):
    form_mapping = {
        'mcq': ExercicioMultiplaEscolhaForm,
        'code': ExercicioCodigoForm, # Usa o nome correto
        'lacuna': ExercicioLacunaForm, # Adiciona o formulário para o novo tipo 'lacuna'
        'vf': ExercicioVerdadeiroFalsoForm,
        # Adicione outros tipos e seus formulários aqui
    }
    return form_mapping.get(tipo_exercicio) # Retorna None se o tipo não estiver no dicionário

@staff_member_required
def listar_exercicios(request):
    exercicios = Exercicio.objects.all() 
    # Filtra os tipos de exercício para não incluir 'info', que não tem formulário de criação.
    tipos_exercicio_disponiveis = [
        {'codigo': tipo_cod, 'nome': tipo_nome} for tipo_cod, tipo_nome in Exercicio.TIPO_CHOICES
        if tipo_cod != 'info'
    ]
    return render(request, 'professor/listar_exercicio.html', {
        'exercicios': exercicios,
        'tipos_exercicio_disponiveis': tipos_exercicio_disponiveis
    })

@staff_member_required
def criar_exercicio(request, tipo_exercicio):
    FormClass = get_exercicio_form_class(tipo_exercicio)
    if not FormClass:
        raise Http404(f"Tipo de exercício '{tipo_exercicio}' não é suportado para criação.")

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            form.save() 
            messages.success(request, f'Exercício do tipo "{dict(Exercicio.TIPO_CHOICES).get(tipo_exercicio)}" criado com sucesso!')
            return redirect('professor:listar_exercicios')
    else:
        form = FormClass() # O __init__ do formulário deve definir o valor inicial para 'tipo'
    
    context = {
        'form': form,
        'tipo_exercicio_nome': dict(Exercicio.TIPO_CHOICES).get(tipo_exercicio, tipo_exercicio.capitalize()),
        'form_title': f"Criar Novo Exercício: {dict(Exercicio.TIPO_CHOICES).get(tipo_exercicio, tipo_exercicio.capitalize())}"
    }
    return render(request, 'professor/criar_exercicio.html', context)

@staff_member_required
def editar_exercicio(request, id):
    exercicio = get_object_or_404(Exercicio, pk=id)
    FormClass = get_exercicio_form_class(exercicio.tipo)

    if not FormClass:
        messages.error(request, f"Não há formulário de edição definido para o tipo de exercício '{exercicio.get_tipo_display()}'.")
        return redirect('professor:listar_exercicios')

    if request.method == 'POST':
        form = FormClass(request.POST, instance=exercicio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exercício atualizado com sucesso!')
            return redirect('professor:listar_exercicios')
    else:
        form = FormClass(instance=exercicio)
    
    context = {
        'form': form,
        'exercicio': exercicio,
        'form_title': f"Editar Exercício: {exercicio.titulo} ({exercicio.get_tipo_display()})"
    }
    return render(request, 'professor/editar_exercicio.html', context)

@staff_member_required
def deletar_exercicio(request, id):
    exercicio = get_object_or_404(Exercicio, pk=id)
    if request.method == 'POST':
        exercicio.delete()
        messages.success(request, 'Exercício excluído com sucesso!')
        return redirect('professor:listar_exercicios')
    
    # Para requisições GET, mostra uma página de confirmação
    return render(request, 'professor/deletar_exercicio_confirm.html', {'exercicio': exercicio})
