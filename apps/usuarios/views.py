from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Perfil, Amizade
from django.db.models import Q
from django.db import models
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .forms import CadastroUsuarioForm
from .models import Conquista
from .services import sincronizar_conquistas



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
def ver_perfil_usuario(request, username):
    """
    Exibe o perfil de um usuário, respeitando sua configuração de privacidade.
    """
    # Busca o usuário pelo username ou retorna 404 se não existir.
    perfil_usuario = get_object_or_404(User, username=username)
    perfil = get_object_or_404(Perfil, user=perfil_usuario)

    # Se o usuário logado está tentando ver seu próprio perfil, redireciona para a view padrão.
    if request.user == perfil_usuario:
        return redirect('usuarios:perfil_usuario')

    # Verifica a configuração de visibilidade do perfil.
    if perfil.visibilidade == 'privado':
        # Se for privado, renderiza uma página informando sobre a privacidade.
        return render(request, 'usuarios/perfil_privado.html', {'perfil': perfil})

    # Se for público, busca os amigos e exibe o perfil completo.
    # (Esta lógica é a mesma da 'perfil_view', mas para o usuário visualizado)
    amizades = Amizade.objects.filter(
        (Q(remetente=perfil_usuario) | Q(destinatario=perfil_usuario)) & Q(status='aceita')
    )
    amigos = [amz.remetente if amz.destinatario == perfil_usuario else amz.destinatario for amz in amizades]

    return render(request, 'usuarios/perfil.html', {'perfil': perfil, 'amigos': amigos})


@login_required
def editar_perfil(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    sincronizar_conquistas(request.user)
    conquistas_desbloqueadas = set(
        perfil.user.conquistas.values_list("conquista__codigo", flat=True)
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'salvar_perfil':
            # Atualiza os dados
            nome = request.POST.get('Nome')
            email = request.POST.get('email')
            bio = request.POST.get('bio')
            avatar = request.POST.get('avatar')

            if not perfil.avatar_desbloqueado(avatar, conquistas_desbloqueadas):
                messages.error(request, "Conclua a conquista necessária para usar este avatar.")
                return redirect('usuarios:editar_perfil')

            user = request.user
            user.username = nome
            user.email = email
            user.save()

            perfil.bio = bio
            if avatar in Perfil.AVATARES:
                perfil.avatar = avatar
            perfil.save()

            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('usuarios:editar_perfil') # Redireciona para a mesma página para ver as alterações.

    
    conquistas = Conquista.objects.in_bulk(field_name="codigo")
    grupos_avatar = []
    for raridade, titulo in [
        ("comum", "Comuns"),
        ("raro", "Raros"),
        ("lendario", "Lendários"),
    ]:
        avatares = []
        for valor, dados in Perfil.AVATARES.items():
            if dados["raridade"] != raridade:
                continue
            conquista = conquistas.get(dados.get("conquista"))
            avatares.append({
                "valor": valor,
                **dados,
                "desbloqueado": perfil.avatar_desbloqueado(valor, conquistas_desbloqueadas),
                "requisito": conquista.descricao if conquista else "Conquista necessária",
            })
        if avatares:
            grupos_avatar.append({"titulo": titulo, "raridade": raridade, "avatares": avatares})

    return render(request, 'usuarios/editar_perfil.html', {
        'perfil': perfil,
        'grupos_avatar': grupos_avatar,
    })




def cadastrar_usuario(request):
    if request.method == "POST":
        form = CadastroUsuarioForm(request.POST)
        if not form.is_valid():
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
            return render(request, "usuarios/cadastro.html", {'form': form})

        username = form.cleaned_data['username']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        visibilidade_choice = request.POST.get('visibilidade')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        # Define o status de visibilidade com base na escolha do usuário
        visibilidade_status = 'privado' if visibilidade_choice == 'privado' else 'publico'
        tempo_estudo = request.session.get('tempo_estudo')
        tempos_estudo_validos = dict(Perfil.TEMPO_ESTUDO_CHOICES)

        # Transfere a preferência escolhida no onboarding para o novo perfil.
        perfil_data = {
            'user': user,
            'visibilidade': visibilidade_status,
        }
        if tempo_estudo in tempos_estudo_validos:
            perfil_data['tempo_estudo'] = tempo_estudo

        Perfil.objects.create(**perfil_data)
        request.session.pop('tempo_estudo', None)

        
        
        messages.success(request, "Cadastro realizado com sucesso!")
        return redirect("usuarios:login_usuario")  # Redireciona para a página de login após o cadastro

    return render(request, "usuarios/cadastro.html", {'form': CadastroUsuarioForm()})



def login_usuario(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect("exercicios:modulos")  # Redirecione para a página desejada
        else:
            messages.error(request, "Usuário ou senha incorretos.", extra_tags="login")

    return render(request, "usuarios/login.html")



@never_cache
def logout_usuario(request):
    # logout() invalida a sessão atual, removendo inclusive seus dados auxiliares.
    logout(request)
    return redirect("usuarios:login_usuario")



@login_required
def amigos(request):
    user = request.user
    perfil = Perfil.objects.get(user=user)

    # Pessoas que o usuário segue (ele foi o remetente da amizade aceita)
    seguindo_amizades = Amizade.objects.filter(remetente=user, status='aceita')
    seguindo = [amizade.destinatario for amizade in seguindo_amizades]

    # Pessoas que seguem o usuário (ele foi o destinatário da amizade aceita)
    seguidores_amizades = Amizade.objects.filter(destinatario=user, status='aceita')
    seguidores = [amizade.remetente for amizade in seguidores_amizades]

    return render(request, 'usuarios/amigos.html', {
        'seguindo': seguindo,
        'seguidores': seguidores,
        'perfil': perfil
    })




@login_required
def encontrar_amigos(request):
    query = request.GET.get('q', None)
    resultados_finais = []
    user = request.user
    
    if query:
        # Busca usuários cujo username contém a query, excluindo o próprio usuário.
        resultados_brutos = User.objects.filter(
            username__icontains=query
        ).exclude(id=user.id).select_related('perfil')

        # Pega todas as relações de amizade do usuário logado para checar o status
        amizades = Amizade.objects.filter(
            Q(remetente=user) | Q(destinatario=user)
        )

        # Mapeia o status por ID de "outro" usuário para busca rápida
        status_map = {}
        for amizade in amizades:
            outro_usuario_id = amizade.destinatario_id if amizade.remetente_id == user.id else amizade.remetente_id
            status_map[outro_usuario_id] = amizade.status

        # Monta a lista final de resultados com o status de cada um
        for u in resultados_brutos:
            status = status_map.get(u.id, 'nenhum') # 'nenhum' = sem relação
            resultados_finais.append({'usuario': u, 'status': status})

    return render(request, 'usuarios/encontrar_amigos.html', {
        'resultados': resultados_finais,
        'query': query,
        'perfil': get_object_or_404(Perfil, user=user)
    })
    
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

@login_required
@require_POST
def enviar_solicitacao_view(request, destinatario_id):
    destinatario = get_object_or_404(User, id=destinatario_id)
    remetente = request.user
    
    # Reutiliza a lógica de negócio para criar a solicitação
    enviar_solicitacao(remetente, destinatario)
    
    messages.success(request, f"Solicitação de amizade enviada para {destinatario.username}.")
    
    # Redireciona de volta para a página de busca, mantendo a query original
    query = request.POST.get('query_original', '')
    redirect_url = reverse('usuarios:encontrar_amigos') + (f'?q={query}' if query else '')
    return redirect(redirect_url)

def solicitacoes_pendentes(request):
    pendentes = Amizade.objects.filter(destinatario=request.user, status='pendente')
    return render(request, "usuarios/solicitacoes.html", {"pendentes": pendentes})



@require_POST
def remover_amigo(request, amigo_id):
    Amizade.objects.filter(
        Q(remetente=request.user, destinatario_id=amigo_id) |
        Q(remetente_id=amigo_id, destinatario=request.user),
        status__in=['aceita', 'pendente']  # inclui pendente também
    ).delete()
    messages.success(request, "Solicitação ou amizade removida.")
    return redirect("usuarios:amigos")







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
