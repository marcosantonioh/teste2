from django.db.models import Sum
from apps.exercicios.models import Exercicio, Modulo, Secao, Estacao, ExercicioUsuario
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
        return estacao.status

    total_exercicios = Exercicio.objects.filter(estacao=estacao).count()
    if total_exercicios == 0:
        return "bloqueado"

    concluidos = ExercicioUsuario.objects.filter(
        usuario=usuario, exercicio__estacao=estacao, status="concluido"
    ).count()
    if concluidos == total_exercicios:
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

    estacao_anterior = secoes[indice - 1]
    total_exercicios_prev = Exercicio.objects.filter(estacao=estacao_anterior).count()
    if total_exercicios_prev == 0:
        return "livre"

    concluidos_prev = ExercicioUsuario.objects.filter(
        usuario=usuario, exercicio__estacao=estacao_anterior, status="concluido"
    ).count()
    return "livre" if concluidos_prev == total_exercicios_prev else "bloqueado"


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
    atualizar_estado_do_perfil_e_exercicio(perfil, exercicio, usuario, correta)
    return "correto" if correta else "incorreto", correta


def marcar_exercicio_concluido(exercicio, perfil, usuario):
    atualizar_estado_do_perfil_e_exercicio(perfil, exercicio, usuario, True)


def verificar_resposta(exercicio, resposta_usuario):
    if exercicio.tipo == "mcq":
        resposta_usuario_str = str(resposta_usuario or "").strip()
        resposta_correta_str = str(exercicio.resposta_correta or "").strip()
        return resposta_usuario_str == resposta_correta_str

    elif exercicio.tipo == "vf":
        resposta_usuario_bool = resposta_usuario == "True"
        return resposta_usuario_bool == exercicio.resposta_vf_correta
    elif exercicio.tipo == "lacuna":
        resposta_usuario_str = str(resposta_usuario or "").strip()
        resposta_correta_str = str(exercicio.resposta_texto_codigo or "").strip()
        return resposta_usuario_str.lower() == resposta_correta_str.lower()
    return False


def obter_ou_criar_progresso(exercicio, usuario):
    if not usuario or not usuario.is_authenticated:
        return None

    progresso, _ = ExercicioUsuario.objects.get_or_create(
        usuario=usuario, exercicio=exercicio, defaults={"status": "livre"}
    )
    return progresso


def atualizar_estado_do_perfil_e_exercicio(perfil, exercicio, usuario, correta):
    if correta:
        progresso = obter_ou_criar_progresso(exercicio, usuario)
        if progresso and progresso.status != "concluido":
            progresso.status = "concluido"
            progresso.save()

            perfil.xp += exercicio.xp
            if perfil.divisao is None and perfil.xp > 0:
                try:
                    divisao_bronze = Divisao.objects.get(nome="Bronze")
                    perfil.divisao = divisao_bronze
                except Divisao.DoesNotExist:
                    pass
            perfil.save()
    else:
        if perfil.vidas_atuais > 0:
            perfil.vidas_atuais -= 1
            perfil.save()


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


def reiniciar_estacao(estacao, usuario):
    if not usuario or not usuario.is_authenticated:
        return

    ExercicioUsuario.objects.filter(
        usuario=usuario, exercicio__estacao=estacao
    ).delete()
