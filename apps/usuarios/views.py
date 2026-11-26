from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Perfil, Amizade
from django.db.models import Q
from django.db import transaction
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .forms import CadastroUsuarioForm, LinksPerfilForm
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

    action = request.POST.get('action') if request.method == 'POST' else None
    abas = {'informacoes', 'preferencias', 'senha', 'links', 'conexoes', 'notificacoes'}
    aba_ativa = request.GET.get('secao', 'informacoes')
    if action:
        aba_ativa = {
            'salvar_perfil': 'informacoes',
            'salvar_preferencias': 'preferencias',
            'alterar_senha': 'senha',
            'salvar_links': 'links',
        }.get(action, aba_ativa)
    if aba_ativa not in abas:
        aba_ativa = 'informacoes'

    senha_form = PasswordChangeForm(
        request.user, request.POST if action == 'alterar_senha' else None
    )
    links_form = LinksPerfilForm(
        request.POST if action == 'salvar_links' else None, instance=perfil
    )

    if request.method == 'POST':

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

        if action == 'salvar_preferencias':
            if _salvar_preferencias(perfil, request.POST):
                messages.success(request, 'Preferências salvas com sucesso!')
                return redirect(reverse('usuarios:editar_perfil') + '?secao=preferencias')
            messages.error(request, 'Escolha um tema e uma visibilidade válidos.')

        if action == 'alterar_senha' and senha_form.is_valid():
            usuario = senha_form.save()
            update_session_auth_hash(request, usuario)
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect(reverse('usuarios:editar_perfil') + '?secao=senha')

        if action == 'salvar_links' and links_form.is_valid():
            links_form.save()
            messages.success(request, 'Links salvos com sucesso!')
            return redirect(reverse('usuarios:editar_perfil') + '?secao=links')

    
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
        'aba_ativa': aba_ativa,
        'senha_form': senha_form,
        'links_form': links_form,
        'amigos': [
            relacao.outro_usuario(request.user)
            for relacao in Amizade.objects.filter(
                Q(remetente=request.user) | Q(destinatario=request.user),
                status=Amizade.STATUS_ACEITA,
            ).select_related('remetente__perfil', 'destinatario__perfil')
        ],
        'solicitacoes_recebidas': Amizade.objects.filter(
            destinatario=request.user, status=Amizade.STATUS_PENDENTE
        ).select_related('remetente__perfil'),
        'solicitacoes_enviadas': Amizade.objects.filter(
            remetente=request.user, status=Amizade.STATUS_PENDENTE
        ).select_related('destinatario__perfil'),
    })


def _salvar_preferencias(perfil, dados):
    tema = dados.get('tema')
    visibilidade = dados.get('visibilidade')
    if tema not in {'claro', 'escuro'} or visibilidade not in {'publico', 'privado'}:
        return False
    perfil.tema = tema
    perfil.visibilidade = visibilidade
    perfil.save(update_fields=['tema', 'visibilidade'])
    return True




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

        meta_ofensiva = request.session.get('meta_ofensiva')
        if request.session.get('demo_concluida') and meta_ofensiva in (7, 14, 30, 50):
            perfil_data.update({
                'meta_ofensiva': meta_ofensiva,
                'xp': 10,
                'cristal': 5,
                'recompensa_demo_recebida': True,
            })

        Perfil.objects.create(**perfil_data)
        request.session.pop('tempo_estudo', None)
        request.session.pop('meta_ofensiva', None)
        request.session.pop('demo_concluida', None)

        
        
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
    perfil = get_object_or_404(Perfil, user=user)
    relacoes = Amizade.objects.filter(
        Q(remetente=user) | Q(destinatario=user),
        status=Amizade.STATUS_ACEITA,
    ).select_related('remetente__perfil', 'destinatario__perfil')
    lista_amigos = [relacao.outro_usuario(user) for relacao in relacoes]
    pendentes = Amizade.objects.filter(
        destinatario=user, status=Amizade.STATUS_PENDENTE
    ).select_related('remetente__perfil')

    return render(request, 'usuarios/amigos.html', {
        'amigos': lista_amigos,
        'pendentes': pendentes,
        'perfil': perfil,
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
            status_map[outro_usuario_id] = {
                'status': amizade.status,
                'direcao': 'enviada' if amizade.remetente_id == user.id else 'recebida',
                'amizade_id': amizade.id,
            }

        # Monta a lista final de resultados com o status de cada um
        for u in resultados_brutos:
            relacao = status_map.get(u.id, {'status': 'nenhum'})
            resultados_finais.append({'usuario': u, **relacao})

    return render(request, 'usuarios/encontrar_amigos.html', {
        'resultados': resultados_finais,
        'query': query,
        'perfil': get_object_or_404(Perfil, user=user)
    })
    
def convidar_amigos(request):
    return render(request, 'usuarios/convidar_amigos.html')


def _redirecionar_apos_acao(request, padrao):
    destino = request.POST.get('next')
    if destino and url_has_allowed_host_and_scheme(destino, {request.get_host()}):
        return redirect(destino)
    return redirect(padrao)


def enviar_solicitacao(remetente, destinatario):
    """Cria uma solicitação, impedindo relações duplicadas em qualquer sentido."""
    if remetente == destinatario:
        return None

    with transaction.atomic():
        existente = Amizade.objects.select_for_update().filter(
            Q(remetente=remetente, destinatario=destinatario)
            | Q(remetente=destinatario, destinatario=remetente)
        ).first()
        if existente:
            return None
        return Amizade.objects.create(remetente=remetente, destinatario=destinatario)

@login_required
@require_POST
def enviar_solicitacao_view(request, destinatario_id):
    destinatario = get_object_or_404(User, id=destinatario_id)
    remetente = request.user
    
    # Reutiliza a lógica de negócio para criar a solicitação.
    if enviar_solicitacao(remetente, destinatario):
        messages.success(request, f"Solicitação de amizade enviada para {destinatario.username}.")
    else:
        messages.error(request, "Não foi possível enviar esta solicitação.")
    
    # Redireciona de volta para a página de busca, mantendo a query original
    query = request.POST.get('query_original', '')
    redirect_url = reverse('usuarios:encontrar_amigos') + (f'?q={query}' if query else '')
    return redirect(redirect_url)

@login_required
@require_POST
def responder_solicitacao(request, amizade_id, resposta):
    amizade = get_object_or_404(
        Amizade,
        id=amizade_id,
        destinatario=request.user,
        status=Amizade.STATUS_PENDENTE,
    )
    amizade.status = (
        Amizade.STATUS_ACEITA if resposta == 'aceitar' else Amizade.STATUS_RECUSADA
    )
    amizade.save(update_fields=['status'])
    messages.success(
        request,
        'Solicitação aceita.' if resposta == 'aceitar' else 'Solicitação recusada.',
    )
    return _redirecionar_apos_acao(request, 'usuarios:amigos')



@login_required
@require_POST
def remover_amigo(request, amigo_id):
    relacao = get_object_or_404(
        Amizade.objects.filter(
            Q(remetente=request.user, destinatario_id=amigo_id)
            | Q(remetente_id=amigo_id, destinatario=request.user),
            status__in=[Amizade.STATUS_ACEITA, Amizade.STATUS_PENDENTE],
        )
    )
    # Apenas quem enviou pode cancelar uma solicitação pendente.
    if relacao.status == Amizade.STATUS_PENDENTE and relacao.remetente_id != request.user.id:
        messages.error(request, 'Use as opções da solicitação para respondê-la.')
    else:
        relacao.delete()
        messages.success(request, 'Solicitação ou amizade removida.')
    return _redirecionar_apos_acao(request, 'usuarios:amigos')







@login_required
def preferencias(request):
    perfil = get_object_or_404(Perfil, user=request.user)

    if request.method == 'POST':
        if _salvar_preferencias(perfil, request.POST):
            messages.success(request, 'Preferências salvas com sucesso!')
        else:
            messages.error(request, 'Escolha um tema e uma visibilidade válidos.')
    return redirect(reverse('usuarios:editar_perfil') + '?secao=preferencias')
