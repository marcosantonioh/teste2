from django.shortcuts import render, get_object_or_404, redirect
from apps.exercicios.models import Exercicio
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import Http404
from apps.exercicios.forms import (
    ExercicioMultiplaEscolhaForm,
    ExercicioCodigoLacunaForm,
    ExercicioCombinacaoForm,
    ExercicioVerdadeiroFalsoForm # Adicionado conforme nossa conversa anterior
)

# Função auxiliar para obter a classe de formulário correta baseada no tipo de exercício
def get_exercicio_form_class(tipo_exercicio):
    if tipo_exercicio == 'mcq':
        return ExercicioMultiplaEscolhaForm
    elif tipo_exercicio == 'code':
        return ExercicioCodigoLacunaForm
    elif tipo_exercicio == 'combinacao':
        return ExercicioCombinacaoForm
    elif tipo_exercicio == 'vf': # Identificador para Verdadeiro ou Falso
        return ExercicioVerdadeiroFalsoForm
    return None

@staff_member_required
def listar_exercicios(request):
    exercicios = Exercicio.objects.all() 
    tipos_exercicio_disponiveis = [
        {'codigo': tipo_cod, 'nome': tipo_nome} for tipo_cod, tipo_nome in Exercicio.TIPO_CHOICES
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
            # O __init__ do formulário já deve definir o 'tipo' com initial e HiddenInput.
            # Se precisar garantir, pode fazer:
            # exercicio = form.save(commit=False)
            # exercicio.tipo = tipo_exercicio
            # exercicio.save()
            # form.save_m2m() # se houver campos many-to-many
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
    exercicio.delete()
    messages.success(request, 'Exercício excluído com sucesso!')
    return redirect('professor:listar_exercicios')
