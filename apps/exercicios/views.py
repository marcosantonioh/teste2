from django.contrib.auth.decorators import login_required
from apps.usuarios.models import Perfil
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from apps.exercicios.models import Exercicio, Modulo, Secao, Estacao
from django.http import Http404



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
        return redirect('etapa', 1)  # ou qual for o nome da sua view inicial

    
    context = {
        'perfil': perfil
    }
    return render( request, 'exercicios/main.html', context)


# @login_required(login_url="usuarios:login_usuario")
def modulos(request):
    perfil = None

    if request.user.is_authenticated:
        try:
            perfil = Perfil.objects.get(user=request.user)
        except ObjectDoesNotExist:
            perfil = Perfil.objects.create(user=request.user)

    modulos = Modulo.objects.all()

    context = {
        'perfil': perfil,  # Vai ser None se o usuário for anônimo
        'modulos': modulos
    }
    return render(request, 'exercicios/modulos.html', context)




def percurso(request, modulo_id):
    
    # Obtém o módulo com o id fornecido
    modulo = get_object_or_404(Modulo, pk=modulo_id)
    secoes = Secao.objects.filter(modulo=modulo)

    perfil = None

    if request.user.is_authenticated:
        try:
            perfil = Perfil.objects.get(user=request.user)
        except ObjectDoesNotExist:
            perfil = Perfil.objects.create(user=request.user)

    # Para cada seção, você pode obter as estações
    for secao in secoes:
        secao.estacoes_list = Estacao.objects.filter(secao=secao)
        for estacao in secao.estacoes_list:
            estacao.exercicios_list = Exercicio.objects.filter(estacao=estacao)

    context = {
        'modulo': modulo,
        'secoes': secoes,
        'perfil': perfil,
    }
    
    # Adicione o módulo ao contexto e renderize o template
    return render(request, 'exercicios/percurso.html', context)





def resolver_exercicio(request, exercicio_id):
    
    try:
        perfil = Perfil.objects.get(user=request.user)
    except Perfil.DoesNotExist:
        raise Http404("Perfil não encontrado")
    
    exercicio = get_object_or_404(Exercicio, id=exercicio_id)

    alternativas = obter_alternativas(exercicio)
    resultado = None
    correta = None
    proximo_exercicio_id_para_continuar = None
    # estacao_totalmente_concluida = False # Não é mais necessário aqui, será tratado com redirect

    exercicios_pendentes = Exercicio.objects.filter(
        estacao=exercicio.estacao,
        status='livre'  # Apenas exercícios livres são considerados pendentes para resolução
    )

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'pular':
            proximo_exercicio = pular_exercicio(exercicio)
            return redirect('exercicios:resolver_exercicio', exercicio_id=proximo_exercicio.id)

        elif acao == 'responder':
            resultado, correta = processar_resposta(request, exercicio, perfil)
            if correta:
                # Encontrar o próximo exercício sequencial na estação
                exercicios_na_estacao = Exercicio.objects.filter(estacao=exercicio.estacao).order_by('id')
                proximo_na_ordem = exercicios_na_estacao.filter(id__gt=exercicio.id).first()

                if proximo_na_ordem:
                    proximo_exercicio_id_para_continuar = proximo_na_ordem.id
                else:
                    # Não há mais exercícios com ID maior nesta estação.
                    # Verificar se todos os exercícios da estação estão concluídos.
                    if not Exercicio.objects.filter(estacao=exercicio.estacao, status='livre').exists():
                        return redirect('exercicios:estacao_concluida', estacao_id=exercicio.estacao.id)
                        

    progresso, exercicios_modulo = calcular_progresso(exercicio.modulo)
    sem_vidas = perfil.vidas <= 0

    context = {
        'exercicio': exercicio,
        'resultado': resultado,
        'correta': correta,
        'perfil': perfil,
        'modulo_id': exercicio.modulo.id,
        'alternativas': alternativas,
        'progresso': progresso,
        'exercicios_modulo': exercicios_modulo,
        'exercicios_pendentes': exercicios_pendentes,
        'proximo_exercicio_id_para_continuar': proximo_exercicio_id_para_continuar, # Ainda útil para o botão continuar normal
        # 'estacao_totalmente_concluida': estacao_totalmente_concluida, # Removido
        'sem_vidas': sem_vidas,
    }

    return render(request, 'exercicios/resolver_exercicio.html', context)


def iniciar_exercicios(request, exercicio_id):
    exercicio = get_object_or_404(Exercicio, id=exercicio_id)
    reiniciar_estacao(request, exercicio)
    return redirect('exercicios:resolver_exercicio', exercicio_id=exercicio.id)


def reiniciar_estacao(request, exercicio):
    """
    Reinicia todos os exercícios da estação do exercício fornecido,
    marcando-os como não concluídos.
    A lógica anterior baseada em sessão foi removida para que sempre reinicie.
    """
    Exercicio.objects.filter(estacao=exercicio.estacao).update(status='livre') # Define como 'livre' para que possam ser resolvidos novamente
    # O parâmetro 'request' é mantido para consistência da assinatura, caso seja usado para logging no futuro.


def pular_exercicio(exercicio):
    pendentes = Exercicio.objects.filter(
        estacao=exercicio.estacao,
        status='livre' # Apenas exercícios livres podem ser pulados/navegados
    ).order_by('id')

    if pendentes.count() > 1:
        proximo = pendentes.filter(id__gt=exercicio.id).first() or pendentes.first()
        return proximo
    return exercicio  # Só um exercício restante




def obter_alternativas(exercicio):
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


def processar_resposta(request, exercicio, perfil):
    resposta = request.POST.get('resposta') if exercicio.tipo == 'mcq' else request.POST.get('codigo', '')
    correta = verificar_resposta(exercicio, resposta)
    atualizar_estado_do_perfil_e_exercicio(perfil, exercicio, correta)
    return ('correto' if correta else 'incorreto'), correta

def verificar_resposta(exercicio, resposta_usuario):
    if exercicio.tipo in ['mcq', 'code']:
        return resposta_usuario.strip() == exercicio.resposta_correta.strip()
    return False


# Em views.py
def atualizar_estado_do_perfil_e_exercicio(perfil, exercicio, correta):
    if correta:
        if exercicio.status != 'concluido': # Só atualiza se não estiver já concluído
            exercicio.status = 'concluido'
            exercicio.save()
            # Lógica de XP, etc.
    else:
        if perfil.vidas > 0:
            perfil.vidas -= 1
            perfil.save()
        # O status do exercício não muda se a resposta for incorreta,
        # a menos que você tenha uma lógica para re-bloquear ou algo assim.


def calcular_progresso(modulo):
    todas_secoes = Secao.objects.filter(modulo=modulo)
    todas_estacoes = Estacao.objects.filter(secao__in=todas_secoes)
    todos_exercicios = Exercicio.objects.filter(estacao__in=todas_estacoes)
    total = todos_exercicios.count()
    concluidos = todos_exercicios.filter(status='concluido').count()
    progresso = int((concluidos / total) * 100) if total > 0 else 0
    return progresso, todos_exercicios.order_by('id')


def estacao_concluida_view(request, estacao_id):
    estacao = get_object_or_404(Estacao, id=estacao_id)
    perfil = None
    if request.user.is_authenticated:
        try:
            perfil = Perfil.objects.get(user=request.user)
        except ObjectDoesNotExist:
            # Lidar com o caso de perfil não existente, talvez criar um ou redirecionar
            pass # Ou redirecionar para login, ou criar perfil

    # Calcular XP total da estação
    exercicios_da_estacao = Exercicio.objects.filter(estacao=estacao)
    total_xp_estacao = exercicios_da_estacao.aggregate(total_xp=Sum('xp'))['total_xp'] or 0

    context = {
        'estacao': estacao,
        'total_xp_estacao': total_xp_estacao,
        'perfil': perfil, # Para a navbar, se necessário
        'modulo_id': estacao.secao.modulo.id, # Para o botão "Voltar ao Percurso"
    }
    return render(request, 'exercicios/estacao_concluida.html', context)
