from django.db.models import Sum
from apps.exercicios.models import Exercicio, Modulo, Secao, Estacao
from apps.usuarios.models import Perfil


def pular_exercicio(exercicio):
    """
    Encontra o próximo exercício 'livre' na mesma estação.
    Se o exercício atual for o último na ordem, volta para o primeiro 'livre'.
    Retorna o exercício atual se for o único 'livre'.
    """
    pendentes = Exercicio.objects.filter(
        estacao=exercicio.estacao, status="livre"
    ).order_by("id")

    if pendentes.count() > 1:
        # Tenta encontrar o próximo com ID maior
        proximo = pendentes.filter(id__gt=exercicio.id).first()
        # Se não houver (ou seja, o atual é o último), pega o primeiro da lista
        return proximo or pendentes.first()

    return exercicio  # Retorna o mesmo exercício se for o único pendente


def processar_resposta_exercicio(resposta_usuario, exercicio, perfil):
    """
    Processa a resposta do usuário, atualiza o estado e retorna o resultado.
    """
    correta = verificar_resposta(exercicio, resposta_usuario)
    atualizar_estado_do_perfil_e_exercicio(perfil, exercicio, correta)
    return "correto" if correta else "incorreto", correta


def verificar_resposta(exercicio, resposta_usuario):
    """
    Verifica se a resposta do usuário para um determinado exercício está correta.
    """
    if exercicio.tipo == "mcq":
        resposta_usuario_str = str(resposta_usuario or "").strip()
        resposta_correta_str = str(exercicio.resposta_correta or "").strip()
        return resposta_usuario_str == resposta_correta_str

    elif exercicio.tipo == "code":
        resposta_usuario_str = str(resposta_usuario or "").strip()
        resposta_correta_str = str(exercicio.resposta_texto_codigo or "").strip()
        return resposta_usuario_str == resposta_correta_str

    elif exercicio.tipo == "vf":
        # Converte a string "True" ou "False" do POST para um booleano Python
        resposta_usuario_bool = resposta_usuario == "True"
        return resposta_usuario_bool == exercicio.resposta_vf_correta

    return False


def atualizar_estado_do_perfil_e_exercicio(perfil, exercicio, correta):
    """
    Atualiza o status do exercício e o perfil do usuário (vidas, XP) com base na resposta.
    """
    if correta:
        if exercicio.status != "concluido":
            exercicio.status = "concluido"
            exercicio.save()
            # Futuramente, adicionar XP aqui:
            # perfil.xp += exercicio.xp
            # perfil.save()
    else:
        if perfil.vidas_atuais > 0:
            perfil.vidas_atuais -= 1
            perfil.save()


def calcular_progresso(modulo):
    """
    Calcula o progresso de conclusão de um módulo em porcentagem.
    """
    todos_exercicios = Exercicio.objects.filter(estacao__secao__modulo=modulo)

    total_exercicios_modulo = todos_exercicios.count()
    if total_exercicios_modulo == 0:
        return 0, 0, 0

    exercicios_concluidos_count = todos_exercicios.filter(status="concluido").count()
    progresso_percentual = int(
        (exercicios_concluidos_count / total_exercicios_modulo) * 100
    )

    return progresso_percentual, exercicios_concluidos_count, total_exercicios_modulo


def reiniciar_estacao(estacao):
    """
    Reinicia todos os exercícios de uma estação, marcando-os como 'livre'.
    """
    Exercicio.objects.filter(estacao=estacao).update(status="livre")
