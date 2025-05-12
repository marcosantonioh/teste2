from django.contrib.auth.decorators import login_required
from apps.usuarios.models import Perfil
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
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
    
    # Verifica se já reiniciou a estação nesta sessão
    session_key = f'estacao_{exercicio.estacao.id}_reiniciada'
    if not request.session.get(session_key, False):
        # Reinicia o progresso da estação
        Exercicio.objects.filter(estacao=exercicio.estacao).update(concluido=False)
        request.session[session_key] = True  # Marca como reiniciada para esta sessão
    
    alternativas = obter_alternativas(exercicio)
    resultado = None
    correta = None

    exercicios_pendentes = Exercicio.objects.filter(
        estacao=exercicio.estacao,
        concluido=False
    )

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'pular':
            # Lista de exercícios ainda não concluídos na mesma estação
            exercicios_pendentes = Exercicio.objects.filter(
                estacao=exercicio.estacao,
                concluido=False
            ).order_by('id')

            # Se houver mais de 1 exercício pendente, procura o próximo após o atual
            if exercicios_pendentes.count() > 1:
                proximo_exercicio = exercicios_pendentes.filter(id__gt=exercicio.id).first()

                # Se não encontrou um ID maior, volta para o primeiro da lista pendente
                if not proximo_exercicio:
                    proximo_exercicio = exercicios_pendentes.first()

                return redirect('exercicios:resolver_exercicio', exercicio_id=proximo_exercicio.id)
            
            else:
                # Só um exercício restante — não há mais para onde pular
                return redirect('exercicios:resolver_exercicio', exercicio_id=exercicio.id)

        elif acao == 'responder':
            resposta_usuario = (
                request.POST.get('resposta') if exercicio.tipo == 'mcq'
                else request.POST.get('codigo', '')
            )
            correta = verificar_resposta(exercicio, resposta_usuario)
            resultado = 'correto' if correta else 'incorreto'
            atualizar_estado_do_perfil_e_exercicio(perfil, exercicio, correta)

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
        'sem_vidas': sem_vidas,
    }

    return render(request, 'exercicios/resolver_exercicio.html', context)



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


def verificar_resposta(exercicio, resposta_usuario):
    if exercicio.tipo == 'mcq':
        return resposta_usuario == exercicio.resposta_correta
    elif exercicio.tipo == 'code':
        return resposta_usuario.strip() == exercicio.resposta_correta.strip()
    return False


def atualizar_estado_do_perfil_e_exercicio(perfil, exercicio, correta):
    if correta:
        if not exercicio.concluido:
            exercicio.concluido = True
            exercicio.save()
    else:
        if perfil.vidas > 0:
            perfil.vidas -= 1
            perfil.save()

def calcular_progresso(modulo):
    todas_secoes = Secao.objects.filter(modulo=modulo)
    todas_estacoes = Estacao.objects.filter(secao__in=todas_secoes)
    todos_exercicios = Exercicio.objects.filter(estacao__in=todas_estacoes)
    total = todos_exercicios.count()
    concluidos = todos_exercicios.filter(concluido=True).count()
    progresso = int((concluidos / total) * 100) if total > 0 else 0
    return progresso, todos_exercicios.order_by('id')

