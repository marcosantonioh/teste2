from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Perfil, Amizade
from django.db.models import Q

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
            return redirect("exercicios:main")  # Redirecione para a página desejada
        else:
            messages.error(request, "Usuário ou senha incorretos.")
    return render(request, "usuarios/login.html")



def logout_usuario(request):
    logout(request)
    return redirect("usuarios:login_usuario")



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
    amizade = Amizade.objects.get(id=amizade_id)
    if amizade.status == 'pendente':
        amizade.status = 'aceita'
        amizade.save()

def aceitar_solicitacao_view(request, amizade_id):
    aceitar_solicitacao(amizade_id)
    return redirect("usuarios:solicitacoes")


def solicitacoes_pendentes(request):
    pendentes = Amizade.objects.filter(destinatario=request.user, status='pendente')
    return render(request, "usuarios/solicitacoes.html", {"pendentes": pendentes})

def remover_amigo(request, amigo_id):
    Amizade.objects.filter(
        Q(remetente=request.user, destinatario_id=amigo_id) |
        Q(remetente_id=amigo_id, destinatario=request.user),
        status='aceita'
    ).delete()
    messages.success(request, "Amizade removida.")
    return redirect("usuarios:lista_amigos")