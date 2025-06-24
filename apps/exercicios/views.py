from django.contrib.auth.decorators import login_required
from apps.usuarios.models import Perfil
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from apps.exercicios.models import Exercicio, Modulo, Secao, Estacao
from apps.mecanicas_jogo import services as mecanicas_services
from django.http import Http404

def get_or_create_perfil(user):
    if not user.is_authenticated:
        return None
    return Perfil.objects.get_or_create(user=user)[0]

# @login_required(login_url="usuarios:login_usuario")
def main_view(request):
    perfil = get_or_create_perfil(request.user)

    # Se o usuário não estiver autenticado E não tiver concluído o onboarding, redireciona
    if not request.user.is_authenticated and not request.session.get('onboarding_concluido'):
        return redirect('etapa', 1)  # ou qual for o nome da sua view inicial

    
    context = {
        'perfil': perfil
    }
    return render( request, 'exercicios/main.html', context)

# @login_required(login_url="usuarios:login_usuario")
def modulos(request):
    perfil = get_or_create_perfil(request.user)
    modulos = Modulo.objects.all()

    context = {
        'perfil': perfil,  # Vai ser None se o usuário for anônimo
        'modulos': modulos
    }
    return render(request, 'exercicios/modulos.html', context)

def percurso(request, modulo_id):
    
    # Obtém o módulo com o id fornecido
    modulo = get_object_or_404(Modulo, pk=modulo_id)
    # Otimização: Usamos prefetch_related para evitar múltiplas queries (problema N+1).
    # Isso busca todas as seções, suas estações e os exercícios de cada estação de forma eficiente.
    secoes = Secao.objects.filter(modulo=modulo).prefetch_related('estacoes__exercicios')
    perfil = get_or_create_perfil(request.user)

    context = {
        'modulo': modulo,
        'secoes': secoes,
        'perfil': perfil,
    }
    
    # Adicione o módulo ao contexto e renderize o template
    return render(request, 'exercicios/percurso.html', context)

def _extrair_resposta_do_request(request, tipo_exercicio):
    """Função auxiliar para extrair a resposta do usuário do objeto request."""
    if tipo_exercicio == 'mcq':
        return request.POST.get('resposta')
    elif tipo_exercicio == 'vf':
        return request.POST.get('resposta_vf')
    return None

def obter_alternativas(exercicio):
    """Prepara a lista de alternativas para exercícios de múltipla escolha."""
    alternativas = []
    if exercicio.alternativa_1:
        alternativas.append(('1', exercicio.alternativa_1))
    if exercicio.alternativa_2:
        alternativas.append(('2', exercicio.alternativa_2))
    if exercicio.alternativa_3:
        alternativas.append(('3', exercicio.alternativa_3))
    if exercicio.alternativa_4:
        alternativas.append(('4', exercicio.alternativa_4))
    return alternativas

def resolver_exercicio(request, exercicio_id):
    perfil = get_or_create_perfil(request.user)
    if not perfil: # Se o usuário não estiver autenticado e a função retornar None
        return redirect('usuarios:login_usuario') # Ou outra lógica de tratamento
    
    exercicio = get_object_or_404(Exercicio, id=exercicio_id)

    alternativas = obter_alternativas(exercicio)
    resultado = None
    correta = None
    proximo_exercicio_id_para_continuar = None
    resposta_submetida = None # Variável para guardar a resposta do usuário

    # Calcular progresso para a barra superior ANTES de qualquer modificação de status.
    # Assim, a barra reflete o estado no momento em que o exercício é exibido.
    progresso_percentual, exercicios_concluidos_count, total_exercicios_modulo = mecanicas_services.calcular_progresso(exercicio.modulo)

    # Lógica para exercícios informativos (tipo 'info')
    # Isso é executado em uma requisição GET, antes do processamento do POST.
    if exercicio.tipo == 'info':
        # Marca o exercício informativo como concluído ao ser visualizado, para não ficar preso nele.
        if exercicio.status == 'livre':
            exercicio.status = 'concluido'
            exercicio.save()
            # Opcional: Adicionar XP se exercícios informativos valerem pontos.
            # perfil.xp_total += exercicio.xp
            # perfil.save()

        # Após marcar como concluído, busca o próximo exercício livre na estação.
        estacao_atual = exercicio.estacao
        proximo_exercicio_livre = Exercicio.objects.filter(
            estacao=estacao_atual,
            status='livre'
        ).order_by('id').first()

        if proximo_exercicio_livre:
            proximo_exercicio_id_para_continuar = proximo_exercicio_livre.id

    # Calcula os exercícios pendentes na estação para usar no template.
    exercicios_pendentes = Exercicio.objects.filter(
        estacao=exercicio.estacao, status='livre'
    )

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'pular':
            proximo_exercicio = mecanicas_services.pular_exercicio(exercicio)
            return redirect('exercicios:resolver_exercicio', exercicio_id=proximo_exercicio.id)

        elif acao == 'responder':
            resposta_usuario = _extrair_resposta_do_request(request, exercicio.tipo)
            resposta_submetida = resposta_usuario  # Guarda a resposta para usar no template
            resultado, correta = mecanicas_services.processar_resposta_exercicio(resposta_usuario, exercicio, perfil)
            if correta:
                estacao_atual = exercicio.estacao
                
                # Após o exercício atual ser marcado como 'concluido' por 
                # atualizar_estado_do_perfil_e_exercicio (chamado em processar_resposta),
                # verificamos se ainda existem outros exercícios 'livre' na estação.
                exercicios_livres_restantes = Exercicio.objects.filter(
                    estacao=estacao_atual,
                    status='livre'  # Busca por exercícios que ainda não foram concluídos
                ).order_by('id')

                if exercicios_livres_restantes.exists():
                    # Se ainda há exercícios livres (incluindo os pulados), 
                    # o botão "Continuar" deve levar ao primeiro deles na ordem de ID.
                    proximo_exercicio_id_para_continuar = exercicios_livres_restantes.first().id
                else:
                    # Não há mais exercícios 'livre', a estação está completa.
                    # Verifica se a estação já não está marcada como completada para evitar saves desnecessários.
                    if estacao_atual.status != 'completado': # Verifica se já não está completado
                        estacao_atual.status = 'completado'
                        estacao_atual.save()
                    return redirect('exercicios:estacao_concluida', estacao_id=estacao_atual.id)

    # Nova lógica para decidir se o modal de saída deve ser mostrado
    mostrar_modal_confirmacao_saida = progresso_percentual > 0

    # Verificar se o usuário não tem mais vidas
    sem_vidas = perfil.vidas_atuais <= 0

    context = {
        'exercicio': exercicio,
        'resultado': resultado,
        'correta': correta,
        'perfil': perfil,
        'modulo_id': exercicio.modulo.id,
        'alternativas': alternativas,
        'resposta_submetida': resposta_submetida, # Passa a resposta do usuário para o template
        'proximo_exercicio_id_para_continuar': proximo_exercicio_id_para_continuar, # Ainda útil para o botão continuar normal
        'sem_vidas': sem_vidas,
        'progresso_percentual': progresso_percentual,
        'exercicios_concluidos_count': exercicios_concluidos_count,
        'total_exercicios_modulo': total_exercicios_modulo,
        'mostrar_modal_confirmacao_saida': mostrar_modal_confirmacao_saida, # Adicionamos aqui
        'exercicios_pendentes': exercicios_pendentes, # Adiciona a variável ao contexto

    }

    return render(request, 'exercicios/resolver_exercicio.html', context)

def iniciar_exercicios(request, exercicio_id):
    exercicio = get_object_or_404(Exercicio, id=exercicio_id)
    mecanicas_services.reiniciar_estacao(exercicio.estacao)
    return redirect('exercicios:resolver_exercicio', exercicio_id=exercicio.id)

def estacao_concluida_view(request, estacao_id):
    estacao = get_object_or_404(Estacao, id=estacao_id)
    perfil = get_or_create_perfil(request.user)
    # Se perfil for None e for necessário para a view, adicione um tratamento aqui.

    # Calcular XP total da estação
    total_xp_estacao = Exercicio.objects.filter(
        estacao=estacao
    ).aggregate(total_xp=Sum('xp'))['total_xp'] or 0

    context = {
        'estacao': estacao,
        'total_xp_estacao': total_xp_estacao,
        'perfil': perfil, # Para a navbar, se necessário
        'modulo_id': estacao.secao.modulo.id, # Para o botão "Voltar ao Percurso"
    }
    return render(request, 'exercicios/estacao_concluida.html', context)
