from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Perfil, Amizade
from django.db.models import Q
from django.db import models
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required



@login_required
def perfil_view(request):
    # Usar get_object_or_404 é uma prática mais segura e padrão no Django.
    user = request.user
    perfil = get_object_or_404(Perfil, user=user)
    
    # Lógica para buscar amigos (reutilizada da view 'amigos')
    amizades = Amizade.objects.filter(
        (Q(remetente=user) | Q(destinatario=user)) & 
        Q(status='aceita')
    )
    amigos = []
    for amizade in amizades:
        if amizade.remetente == user:
            amigos.append(amizade.destinatario)
        else:
            amigos.append(amizade.remetente)
            
    return render(request, 'usuarios/perfil.html', {'perfil': perfil, 'amigos': amigos})


@login_required
def editar_perfil(request):
    perfil = get_object_or_404(Perfil, user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'salvar_perfil':
            # Atualiza os dados
            nome = request.POST.get('Nome')
            email = request.POST.get('email')
            bio = request.POST.get('bio')
            nova_foto = request.FILES.get('foto')

            user = request.user
            user.username = nome
            user.email = email
            user.save()

            perfil.bio = bio
            if nova_foto:
                perfil.foto = nova_foto
            perfil.save()

            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('usuarios:editar_perfil') # Redireciona para a mesma página para ver as alterações.

        if action == "deletar_foto":
            if perfil.foto:
                perfil.foto.delete(save=False)  # deleta o arquivo físico
                perfil.foto = None              # remove do modelo
                perfil.save()
            return redirect('usuarios:editar_perfil')
    
    return render(request, 'usuarios/editar_perfil.html', {'perfil': perfil}) # Passa o perfil no GET também




def cadastrar_usuario(request):
    if request.method == "POST":
        # Coletando os dados do formulário
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        password2 = request.POST["password2"]
        foto = request.FILES.get("foto")  # pega a imagem enviada no form

        
        
        # Verificando se as senhas coincidem
        if password != password2:
            messages.error(request, "As senhas não coincidem!")
            return redirect("usuarios:cadastro_usuario")  # Redireciona de volta ao formulário de cadastro
        
        # Verificar se o nome de usuário já existe
        if User.objects.filter(username=username).exists():
            messages.error(request, "Nome de usuário já está em uso. Escolha outro.")
            return redirect("usuarios:cadastro_usuario")
       
        # Verificando se o e-mail já está registrado
        if User.objects.filter(email=email).exists():
            messages.error(request, "Este e-mail já está cadastrado!")
            return redirect("usuarios:cadastro_usuario")
    
        # Criando o usuário
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # Criar o perfil associado ao usuário e com foto se tiver
        Perfil.objects.create(user=user, foto=foto)

        
        
        messages.success(request, "Cadastro realizado com sucesso!")
        return redirect("usuarios:login_usuario")  # Redireciona para a página de login após o cadastro


    return render(request, "usuarios/cadastro.html")



def login_usuario(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect("exercicios:modulos")  # Redirecione para a página desejada
        else:
            messages.error(request, "Usuário ou senha incorretos.")
    return render(request, "usuarios/login.html")



def logout_usuario(request):
    logout(request)
    return redirect("usuarios:login_usuario")



@login_required
def amigos(request):
    user = request.user
    perfil = Perfil.objects.get(user=user)
    amizades = Amizade.objects.filter(
        (Q(remetente=user) | Q(destinatario=user)) & 
        Q(status='aceita')
    )
    amigos = []
    for amizade in amizades:
        if amizade.remetente == user:
            amigos.append(amizade.destinatario)
        else:
            amigos.append(amizade.remetente)

    return render(request, 'usuarios/amigos.html', {
        'amigos': amigos,
        'perfil': perfil
    })




def encontrar_amigos(request):
    return render(request, 'usuarios/encontrar_amigos.html')
    
def convidar_amigos(request):
    return render(request, 'usuarios/convidar_amigos.html')


def enviar_solicitacao(remetente, destinatario):
    if remetente != destinatario:
        # Verifica se já existe uma solicitação em qualquer direção
        existente = Amizade.objects.filter(
            Q(remetente=remetente, destinatario=destinatario) |
            Q(remetente=destinatario, destinatario=remetente)
        ).exists()

        if not existente:
            amizade = Amizade.objects.create(remetente=remetente, destinatario=destinatario)
            return amizade


def aceitar_solicitacao(amizade_id):
    amizade = get_object_or_404(Amizade, id=amizade_id)
    if amizade.status == 'pendente':
        amizade.status = 'aceita'
        amizade.save()

def aceitar_solicitacao_view(request, amizade_id):
    aceitar_solicitacao(amizade_id)
    return redirect("usuarios:solicitacoes")


def solicitacoes_pendentes(request):
    pendentes = Amizade.objects.filter(destinatario=request.user, status='pendente')
    return render(request, "usuarios/solicitacoes.html", {"pendentes": pendentes})


@require_POST
def remover_amigo(request, amigo_id):
    Amizade.objects.filter(
        Q(remetente=request.user, destinatario_id=amigo_id) |
        Q(remetente_id=amigo_id, destinatario=request.user),
        status='aceita'
    ).delete()
    messages.success(request, "Amizade removida.")
    return redirect("usuarios:lista_amigos")







@login_required
def preferencias(request):
    perfil = get_object_or_404(Perfil, user=request.user)

    if request.method == 'POST':
        tema = request.POST.get('tema')
        visibilidade = request.POST.get('visibilidade')

        perfil.tema = tema
        perfil.visibilidade = visibilidade
        perfil.save()

        messages.success(request, 'Preferências salvas com sucesso!')
        return redirect('usuarios:preferencias')

    # Adiciona o perfil ao contexto para que o template possa exibir os valores atuais.
    context = {'perfil': perfil}
    return render(request, 'usuarios/preferencias.html', context)