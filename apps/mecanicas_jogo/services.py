from django.db.models import Sum
from apps.exercicios.models import (
    BauEstacaoUsuario,
    Exercicio,
    Modulo,
    Secao,
    Estacao,
    ExercicioUsuario,
)
from apps.usuarios.models import Divisao


def obter_status_exercicio(exercicio, usuario):
    if not usuario or not usuario.is_authenticated:
        return exercicio.status

    progresso = ExercicioUsuario.objects.filter(
        usuario=usuario, exercicio=exercicio
    ).first()
    return progresso.status if progresso else "livre"


def obter_exercicios_nao_concluidos(estacao, usuario):
    exercicios = Exercicio.objects.filter(estacao=estacao).order_by("id")
    if not usuario or not usuario.is_authenticated:
        return exercicios.filter(status="livre")

    concluidos_ids = ExercicioUsuario.objects.filter(
        usuario=usuario, exercicio__estacao=estacao, status="concluido"
    ).values_list("exercicio_id", flat=True)
    return exercicios.exclude(id__in=concluidos_ids)


def obter_status_estacao(estacao, usuario):
    if not usuario or not usuario.is_authenticated:
        return "bloqueado"

    # Uma seção só pode ser iniciada quando todas as seções anteriores do
    # módulo tiverem sido concluídas pelo próprio usuário.
    if not secao_esta_liberada(estacao.secao, usuario):
        return "bloqueado"

    total_exercicios = Exercicio.objects.filter(estacao=estacao).count()
    if total_exercicios == 0:
        return "bloqueado"

    concluidos = ExercicioUsuario.objects.filter(
        usuario=usuario, exercicio__estacao=estacao, status="concluido"
    ).count()
    if concluidos >= total_exercicios:
        return "completado"

    secoes = list(Estacao.objects.filter(secao=estacao.secao).order_by("id"))
    if not secoes:
        return "bloqueado"

    if secoes[0] == estacao:
        return "livre"

    try:
        indice = secoes.index(estacao)
    except ValueError:
        return "bloqueado"

    # O terceiro ponto do percurso é liberado pela coleta do baú que aparece
    # após a segunda estação. As demais estações seguem a regra normal.
    if indice == 2 and not BauEstacaoUsuario.objects.filter(
        usuario=usuario, secao=estacao.secao
    ).exists():
        return "bloqueado"

    estacao_anterior = secoes[indice - 1]
    total_exercicios_prev = Exercicio.objects.filter(estacao=estacao_anterior).count()
    if total_exercicios_prev == 0:
        return "livre"

    concluidos_prev = ExercicioUsuario.objects.filter(
        usuario=usuario, exercicio__estacao=estacao_anterior, status="concluido"
    ).count()
    return "livre" if concluidos_prev == total_exercicios_prev else "bloqueado"


def secao_esta_concluida(secao, usuario):
    """Informa se o usuário concluiu todas as estações da seção."""
    estacoes = Estacao.objects.filter(secao=secao).order_by("id")
    if not estacoes.exists():
        return False

    return all(
        obter_status_estacao(estacao, usuario) == "completado"
        for estacao in estacoes
    )


def secao_esta_liberada(secao, usuario):
    """Uma seção é liberada somente após a conclusão de suas antecessoras."""
    if not usuario or not usuario.is_authenticated:
        return False

    secoes_anteriores = Secao.objects.filter(
        modulo=secao.modulo, ordem__lt=secao.ordem
    ).order_by("ordem", "id")

    # Trata também seções com a mesma ordem, mantendo a ordenação do modelo.
    secoes_anteriores = list(secoes_anteriores) + list(
        Secao.objects.filter(modulo=secao.modulo, ordem=secao.ordem, id__lt=secao.id)
        .order_by("id")
    )
    return all(
        secao_esta_concluida(anterior, usuario) for anterior in secoes_anteriores
    )


def pular_exercicio(exercicio, usuario):
    pendentes = obter_exercicios_nao_concluidos(exercicio.estacao, usuario).order_by(
        "id"
    )

    if pendentes.count() > 1:
        proximo = pendentes.filter(id__gt=exercicio.id).first()
        return proximo or pendentes.first()

    return exercicio


def processar_resposta_exercicio(resposta_usuario, exercicio, perfil, usuario):
    correta = verificar_resposta(exercicio, resposta_usuario)
    conquistas_novas = atualizar_estado_do_perfil_e_exercicio(
        perfil, exercicio, usuario, correta
    )
    return "correto" if correta else "incorreto", correta, conquistas_novas


def marcar_exercicio_concluido(exercicio, perfil, usuario):
    return atualizar_estado_do_perfil_e_exercicio(exercicio=exercicio, perfil=perfil, usuario=usuario, correta=True)


def verificar_resposta(exercicio, resposta_usuario):
    if exercicio.tipo == "mcq":
        resposta_usuario_str = str(resposta_usuario or "").strip()
        resposta_correta_str = str(exercicio.resposta_correta or "").strip()
        return resposta_usuario_str == resposta_correta_str

    elif exercicio.tipo == "vf":
        resposta_usuario_bool = resposta_usuario == "True"
        return resposta_usuario_bool == exercicio.resposta_vf_correta
    elif exercicio.tipo == "lacuna":
        resposta_normalizada = normalizar_resposta_lacuna(resposta_usuario)
        respostas_aceitas = [exercicio.resposta_texto_codigo, *exercicio.respostas_aceitas]
        return resposta_normalizada in {
            normalizar_resposta_lacuna(resposta)
            for resposta in respostas_aceitas
            if resposta
        }
    return False


def normalizar_resposta_lacuna(resposta):
    """Compara código de lacuna sem diferenças irrelevantes de formato."""
    resposta = str(resposta or "").strip().lower()
    resposta = resposta.rstrip(";").strip()
    return "".join(resposta.split())


def obter_ou_criar_progresso(exercicio, usuario):
    if not usuario or not usuario.is_authenticated:
        return None

    progresso, _ = ExercicioUsuario.objects.get_or_create(
        usuario=usuario, exercicio=exercicio, defaults={"status": "livre"}
    )
    return progresso


def estacao_esta_concluida(estacao, usuario):
    """Informa se todos os exercícios da estação foram concluídos pelo usuário."""
    total_exercicios = Exercicio.objects.filter(estacao=estacao).count()
    if total_exercicios == 0:
        return False

    concluidos = ExercicioUsuario.objects.filter(
        usuario=usuario, exercicio__estacao=estacao, status="concluido"
    ).count()
    return concluidos == total_exercicios


def atualizar_estado_do_perfil_e_exercicio(perfil, exercicio, usuario, correta):
    if correta:
        progresso = obter_ou_criar_progresso(exercicio, usuario)
        if progresso and progresso.status != "concluido":
            progresso.status = "concluido"
            deve_conceder_xp = not progresso.xp_concedido

            if deve_conceder_xp:
                progresso.xp_concedido = True
            progresso.save(update_fields=["status", "xp_concedido", "atualizado_em"])

            # Ao reiniciar uma estação, o status volta a "livre" para treino,
            # mas xp_concedido permanece verdadeiro. Assim, o mesmo exercício
            # nunca entrega XP duas vezes para o mesmo usuário.
            conquistas_novas = []
            if deve_conceder_xp:
                perfil.xp += exercicio.xp
                if perfil.divisao is None and perfil.xp > 0:
                    try:
                        divisao_bronze = Divisao.objects.get(nome="Bronze")
                        perfil.divisao = divisao_bronze
                    except Divisao.DoesNotExist:
                        pass
                perfil.save()
                from apps.usuarios.services import sincronizar_conquistas

                conquistas_novas = sincronizar_conquistas(usuario)

            # A ofensiva é contabilizada somente ao concluir toda a estação,
            # e o próprio perfil limita o ganho a uma vez por dia.
            if estacao_esta_concluida(exercicio.estacao, usuario):
                perfil.registrar_estacao_concluida()

            return conquistas_novas
    else:
        if perfil.vidas_atuais > 0:
            perfil.vidas_atuais -= 1
            perfil.save()
    return []


def calcular_progresso(modulo, usuario):
    todos_exercicios = Exercicio.objects.filter(estacao__secao__modulo=modulo)
    total_exercicios_modulo = todos_exercicios.count()
    if total_exercicios_modulo == 0:
        return 0, 0, 0

    if not usuario or not usuario.is_authenticated:
        return 0, 0, total_exercicios_modulo

    exercicios_concluidos_count = ExercicioUsuario.objects.filter(
        usuario=usuario, exercicio__estacao__secao__modulo=modulo, status="concluido"
    ).count()
    progresso_percentual = int(
        (exercicios_concluidos_count / total_exercicios_modulo) * 100
    )
    return progresso_percentual, exercicios_concluidos_count, total_exercicios_modulo


def calcular_progresso_estacao(estacao, usuario):
    exercicios_estacao = Exercicio.objects.filter(estacao=estacao)
    total_exercicios_estacao = exercicios_estacao.count()
    if total_exercicios_estacao == 0:
        return 0, 0, 0

    if not usuario or not usuario.is_authenticated:
        return 0, 0, total_exercicios_estacao

    exercicios_concluidos_count = ExercicioUsuario.objects.filter(
        usuario=usuario, exercicio__estacao=estacao, status="concluido"
    ).count()
    progresso_percentual = int(
        (exercicios_concluidos_count / total_exercicios_estacao) * 100
    )
    return progresso_percentual, exercicios_concluidos_count, total_exercicios_estacao


def reiniciar_estacao(estacao, usuario):
    if not usuario or not usuario.is_authenticated:
        return

    # Preserva o histórico de XP. Apenas o estado de conclusão é reiniciado
    # para que a estação possa ser praticada novamente.
    ExercicioUsuario.objects.filter(
        usuario=usuario, exercicio__estacao=estacao
    ).update(status="livre")
