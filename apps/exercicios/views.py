import random

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from apps.usuarios.models import Perfil
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from apps.exercicios.models import (
    Exercicio,
    ExercicioUsuario,
    Modulo,
    Secao,
    Estacao,
    ReporteExercicio,
)
from apps.mecanicas_jogo import services as mecanicas_services
from apps.desafios.models import DesafioUsuario
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.template.defaultfilters import linebreaksbr  # Para formatar o enunciado
from django.templatetags.static import static
from django.utils.html import escape, mark_safe

CHAVE_ORDEM_ALTERNATIVAS = "ordens_alternativas_mcq"
CHAVE_ULTIMA_ORDEM_ALTERNATIVAS = "ultimas_ordens_alternativas_mcq"


def get_or_create_perfil(user):
    if not user.is_authenticated:
        return None
    return Perfil.objects.get_or_create(user=user)[0]


def serializar_conquistas_novas(conquistas):
    """Prepara as novas conquistas para o modal exibido após a resposta."""
    conquistas_serializadas = []
    for conquista in conquistas or []:
        avatar = next(
            (
                dados
                for dados in Perfil.AVATARES.values()
                if dados.get("conquista") == conquista.codigo
            ),
            None,
        )
        conquistas_serializadas.append(
            {
                "nome": conquista.nome,
                "descricao": conquista.descricao,
                "avatar_url": static(avatar["arquivo"]) if avatar else None,
                "avatar_nome": avatar["nome"] if avatar else None,
            }
        )
    return conquistas_serializadas


# @login_required(login_url="usuarios:login_usuario")
def main_view(request):
    perfil = get_or_create_perfil(request.user)

    # Se o usuário não estiver autenticado E não tiver concluído o onboarding, redireciona
    if not request.user.is_authenticated and not request.session.get(
        "onboarding_concluido"
    ):
        return redirect("etapa", 1)  # ou qual for o nome da sua view inicial

    context = {"perfil": perfil}
    return render(request, "exercicios/main.html", context)


@login_required
def modulos(request):
    perfil = get_or_create_perfil(request.user)
    modulos = Modulo.objects.exclude(
        secoes__estacoes__disponivel_para_visitantes=True
    ).distinct()

    # Busca os desafios do usuário logado
    desafios_usuario = DesafioUsuario.objects.filter(usuario=request.user)

    # Calcula o progresso em porcentagem
    for du in desafios_usuario:
        try:
            du.porcentagem = int((du.progresso / du.desafio.meta) * 100)
        except ZeroDivisionError:
            du.porcentagem = 0

    context = {
        "perfil": perfil,
        "modulos": modulos,
        "desafios_usuario": desafios_usuario,
    }

    return render(request, "exercicios/modulos.html", context)


@login_required
def percurso(request, modulo_id):
    modulo = get_object_or_404(Modulo, pk=modulo_id)
    perfil = get_or_create_perfil(request.user)

    secoes = list(Secao.objects.filter(modulo=modulo).order_by("ordem", "id"))
    secao_atual = next(
        (
            secao
            for secao in secoes
            if not mecanicas_services.secao_esta_concluida(secao, request.user)
        ),
        None,
    )

    secoes_mapa = []
    for secao in secoes:
        estacoes_secao = list(secao.estacoes.all())
        estacoes_concluidas = sum(
            mecanicas_services.obter_status_estacao(estacao, request.user)
            == "completado"
            for estacao in estacoes_secao
        )
        total_estacoes = len(estacoes_secao)
        progresso_percentual = (
            int((estacoes_concluidas / total_estacoes) * 100)
            if total_estacoes
            else 0
        )

        if estacoes_concluidas == total_estacoes and total_estacoes:
            estado_mapa = "concluida"
        elif secao == secao_atual:
            estado_mapa = "atual"
        else:
            estado_mapa = "bloqueada"
        secoes_mapa.append(
            {
                "secao": secao,
                "estado": estado_mapa,
                "estacoes_concluidas": estacoes_concluidas,
                "total_estacoes": total_estacoes,
                "progresso_percentual": progresso_percentual,
            }
        )

    # Ao terminar o módulo, mantém a última seção visível como referência.
    if secao_atual is None and secoes:
        secao_atual = secoes[-1]

    proxima_secao = None
    estacoes = []
    estacao_animada_id = None
    if secao_atual:
        indice_atual = secoes.index(secao_atual)
        if indice_atual + 1 < len(secoes):
            proxima_secao = secoes[indice_atual + 1]

        estacoes = list(secao_atual.estacoes.prefetch_related("exercicios").all())
        for estacao in estacoes:
            estacao.status = mecanicas_services.obter_status_estacao(
                estacao, request.user
            )

        estacao_livre = next(
            (estacao for estacao in estacoes if estacao.status == "livre"), None
        )
        if estacao_livre:
            estacao_animada_id = estacao_livre.id
        else:
            for indice, estacao in enumerate(estacoes[:-1]):
                proxima_estacao = estacoes[indice + 1]
                if (
                    estacao.status == "completado"
                    and proxima_estacao.status == "bloqueado"
                ):
                    estacao_animada_id = estacao.id
                    break

    context = {
        "modulo": modulo,
        "secao_atual": secao_atual,
        "estacoes": estacoes,
        "estacao_animada_id": estacao_animada_id,
        "proxima_secao": proxima_secao,
        "perfil": perfil,
        "secoes_mapa": secoes_mapa,
        "visualizar_todas_secoes": request.GET.get("visualizacao") == "todas",
    }

    # Adicione o módulo ao contexto e renderize o template
    return render(request, "exercicios/percurso.html", context)


def _extrair_resposta_do_request(request, tipo_exercicio):
    """Função auxiliar para extrair a resposta do usuário do objeto request."""
    if tipo_exercicio in ["mcq", "lacuna"]:
        return request.POST.get("resposta")
    elif tipo_exercicio == "vf":
        return request.POST.get("resposta_vf")
    return None


def _marcador_lacuna(exercicio, resposta_submetida=None):
    """Cria a lacuna com largura proporcional à resposta esperada.

    Somente o tamanho é enviado ao navegador; a resposta correta permanece no
    banco. Um input nativo torna a digitação acessível e previsível dentro do
    trecho de código, sem revelar a resposta nem usar sublinhados.
    """
    resposta_esperada = (exercicio.resposta_texto_codigo or "").strip()
    tamanho_lacuna = max(1, len(resposta_esperada))
    texto_exibido = resposta_submetida or ""

    return (
        '<input type="text" class="lacuna-marker" name="resposta" '
        'aria-label="Resposta da lacuna" autocomplete="off" '
        'spellcheck="false" '
        f'style="--tamanho-lacuna: {tamanho_lacuna}" '
        f'value="{escape(texto_exibido)}">'
    )


def obter_alternativas(exercicio, request=None):
    """Retorna as alternativas na ordem da tentativa atual do usuário.

    A identificação de cada alternativa continua sendo o número originalmente
    salvo no exercício. Assim, mudar a posição visual não afeta a validação da
    resposta correta.
    """
    alternativas = []
    if exercicio.alternativa_1:
        alternativas.append(("1", exercicio.alternativa_1))
    if exercicio.alternativa_2:
        alternativas.append(("2", exercicio.alternativa_2))
    if exercicio.alternativa_3:
        alternativas.append(("3", exercicio.alternativa_3))
    if exercicio.alternativa_4:
        alternativas.append(("4", exercicio.alternativa_4))

    if request is None or len(alternativas) < 2:
        return alternativas

    chave_exercicio = str(exercicio.id)
    ordens_salvas = request.session.get(CHAVE_ORDEM_ALTERNATIVAS, {})
    ultimas_ordens = request.session.get(CHAVE_ULTIMA_ORDEM_ALTERNATIVAS, {})
    ordem_salva = ordens_salvas.get(chave_exercicio)
    numeros_alternativas = [numero for numero, _ in alternativas]

    ordem_eh_valida = (
        isinstance(ordem_salva, list)
        and len(ordem_salva) == len(numeros_alternativas)
        and set(ordem_salva) == set(numeros_alternativas)
    )

    if not ordem_eh_valida:
        ordem_salva = numeros_alternativas[:]
        random.shuffle(ordem_salva)

        if ordem_salva == ultimas_ordens.get(chave_exercicio):
            ordem_salva = ordem_salva[1:] + ordem_salva[:1]

        ordens_salvas[chave_exercicio] = ordem_salva
        request.session[CHAVE_ORDEM_ALTERNATIVAS] = ordens_salvas

    alternativas_por_numero = dict(alternativas)
    return [(numero, alternativas_por_numero[numero]) for numero in ordem_salva]


def _estacao_demonstracao():
    return get_object_or_404(Estacao, disponivel_para_visitantes=True)


def _exercicios_demonstracao(estacao):
    return list(estacao.exercicios.order_by("id"))


def iniciar_demonstracao(request):
    """Inicia uma experiência limitada e sem persistência para visitantes."""
    if request.user.is_authenticated:
        return redirect("exercicios:modulos")
    if not request.session.get("onboarding_concluido"):
        return redirect("landing")

    exercicios = _exercicios_demonstracao(_estacao_demonstracao())
    if not exercicios:
        return redirect("landing")
    return redirect("exercicios:resolver_demo", exercicio_id=exercicios[0].id)


def resolver_demonstracao(request, exercicio_id):
    """Exibe e corrige exercícios de demonstração sem alterar dados do jogo."""
    if request.user.is_authenticated:
        return redirect("exercicios:modulos")
    if not request.session.get("onboarding_concluido"):
        return redirect("landing")

    estacao = _estacao_demonstracao()
    exercicio = get_object_or_404(Exercicio, id=exercicio_id, estacao=estacao)
    exercicios = _exercicios_demonstracao(estacao)
    indice_atual = exercicios.index(exercicio)
    proximo_exercicio = (
        exercicios[indice_atual + 1] if indice_atual + 1 < len(exercicios) else None
    )

    resposta_submetida = None
    correta = None
    if request.method == "POST" and exercicio.tipo != "info":
        resposta_submetida = _extrair_resposta_do_request(request, exercicio.tipo)
        correta = mecanicas_services.verificar_resposta(exercicio, resposta_submetida)

    if exercicio.tipo == "mcq":
        alternativas = obter_alternativas(exercicio, request)
        campo_resposta = "resposta"
        resposta_correta = exercicio.resposta_correta
    elif exercicio.tipo == "vf":
        alternativas = [("True", "Verdadeiro"), ("False", "Falso")]
        campo_resposta = "resposta_vf"
        resposta_correta = str(exercicio.resposta_vf_correta)
    elif exercicio.tipo == "lacuna":
        alternativas = []
        campo_resposta = "resposta"
        resposta_correta = exercicio.resposta_texto_codigo
    else:
        alternativas = []
        campo_resposta = None
        resposta_correta = None

    return render(
        request,
        "exercicios/demonstracao.html",
        {
            "estacao": estacao,
            "exercicio": exercicio,
            "alternativas": alternativas,
            "campo_resposta": campo_resposta,
            "resposta_correta": resposta_correta,
            "resposta_submetida": resposta_submetida,
            "correta": correta,
            "proximo_exercicio": proximo_exercicio,
            "indice_exercicio": indice_atual + 1,
            "total_exercicios": len(exercicios),
        },
    )


def limpar_ordens_alternativas_da_estacao(request, estacao):
    """Remove a ordem da tentativa anterior ao reiniciar uma estação."""
    ordens_salvas = request.session.get(CHAVE_ORDEM_ALTERNATIVAS, {})
    ultimas_ordens = request.session.get(CHAVE_ULTIMA_ORDEM_ALTERNATIVAS, {})
    houve_alteracao = False

    for exercicio_id in estacao.exercicios.values_list("id", flat=True):
        chave_exercicio = str(exercicio_id)
        ordem_anterior = ordens_salvas.pop(chave_exercicio, None)
        if ordem_anterior is not None:
            ultimas_ordens[chave_exercicio] = ordem_anterior
            houve_alteracao = True

    if houve_alteracao:
        request.session[CHAVE_ORDEM_ALTERNATIVAS] = ordens_salvas
        request.session[CHAVE_ULTIMA_ORDEM_ALTERNATIVAS] = ultimas_ordens


def _obter_resumo_estacao(request, estacao_id):
    resumo_estacoes = request.session.setdefault("resumo_estacoes", {})
    chave = str(estacao_id)
    estacao_atual_id = request.session.get("estacao_resumo_atual_id")
    total_exercicios = Exercicio.objects.filter(estacao_id=estacao_id).count()

    if estacao_atual_id != chave or chave not in resumo_estacoes:
        resumo_estacoes[chave] = {
            "acertos": 0,
            "erros": 0,
            "xp_ganho": 0,
            "total_exercicios": total_exercicios,
        }
        request.session["estacao_resumo_atual_id"] = chave
    else:
        resumo_estacoes[chave]["total_exercicios"] = total_exercicios

    request.session["resumo_estacoes"] = resumo_estacoes
    return resumo_estacoes[chave]


def _atualizar_resumo_estacao(request, estacao_id, correta, exercicio):
    resumo = _obter_resumo_estacao(request, estacao_id)

    if correta:
        resumo["acertos"] += 1
        resumo["xp_ganho"] += int(exercicio.xp or 0)
    else:
        resumo["erros"] += 1

    if resumo["total_exercicios"] == 0:
        resumo["total_exercicios"] = Exercicio.objects.filter(
            estacao_id=estacao_id
        ).count()

    request.session["resumo_estacoes"][str(estacao_id)] = resumo
    return resumo


def resolver_exercicio(request, exercicio_id):
    perfil = get_or_create_perfil(request.user)
    if not perfil:  # Se o usuário não estiver autenticado e a função retornar None
        return redirect("usuarios:login_usuario")  # Ou outra lógica de tratamento

    exercicio = get_object_or_404(Exercicio, id=exercicio_id)
    if (
        mecanicas_services.obter_status_estacao(exercicio.estacao, request.user)
        == "bloqueado"
    ):
        raise PermissionDenied("Esta estação ainda está bloqueada.")

    alternativas = obter_alternativas(exercicio, request)
    resultado = None
    correta = None
    proximo_exercicio_id_para_continuar = None
    resposta_submetida = None  # Variável para guardar a resposta do usuário
    conquistas_novas = []

    # Calcular progresso para a barra superior ANTES de qualquer modificação de status.
    # Assim, a barra reflete o estado no momento em que o exercício é exibido.
    progresso_percentual, exercicios_concluidos_count, total_exercicios_modulo = (
        mecanicas_services.calcular_progresso_estacao(exercicio.estacao, request.user)
    )

    # Lógica para exercícios informativos (tipo 'info')
    # Isso é executado em uma requisição GET, antes do processamento do POST.
    if exercicio.tipo == "info":
        # Marca o exercício informativo como concluído ao ser visualizado, para não ficar preso nele.
        if (
            mecanicas_services.obter_status_exercicio(exercicio, request.user)
            == "livre"
        ):
            conquistas_novas = mecanicas_services.marcar_exercicio_concluido(
                exercicio, perfil, request.user
            )
            _atualizar_resumo_estacao(
                request, exercicio.estacao_id, True, exercicio
            )

        # Após marcar como concluído, busca o próximo exercício livre na estação.
        estacao_atual = exercicio.estacao
        proximo_exercicio_livre = (
            mecanicas_services.obter_exercicios_nao_concluidos(
                estacao_atual, request.user
            )
            .order_by("id")
            .first()
        )

        if proximo_exercicio_livre:
            proximo_exercicio_id_para_continuar = proximo_exercicio_livre.id

    # Calcula os exercícios pendentes na estação para usar no template.
    exercicios_pendentes = mecanicas_services.obter_exercicios_nao_concluidos(
        exercicio.estacao, request.user
    )

    if request.method == "POST":

        # Verificamos se a requisição veio do nosso script (AJAX)
        is_ajax = request.POST.get("is_ajax_request") == "1"

        acao = request.POST.get("acao")

        if acao == "pular":
            proximo_exercicio = mecanicas_services.pular_exercicio(
                exercicio, request.user
            )
            return redirect(
                "exercicios:resolver_exercicio", exercicio_id=proximo_exercicio.id
            )

        elif acao == "responder":
            resposta_usuario = _extrair_resposta_do_request(request, exercicio.tipo)

            resultado, correta, conquistas_novas = mecanicas_services.processar_resposta_exercicio(
                resposta_usuario, exercicio, perfil, request.user
            )
            resumo_estacao = _atualizar_resumo_estacao(
                request, exercicio.estacao_id, correta, exercicio
            )

            # Se for uma requisição AJAX, vamos montar e retornar uma resposta JSON.
            if is_ajax:
                proximo_exercicio_id = None
                estacao_concluida_url = None
                mostrar_resumo_estacao = False

                if correta:
                    estacao_atual = exercicio.estacao
                    exercicios_livres_restantes = (
                        mecanicas_services.obter_exercicios_nao_concluidos(
                            estacao_atual, request.user
                        ).order_by("id")
                    )

                    if exercicios_livres_restantes.exists():
                        proximo_exercicio_id = exercicios_livres_restantes.first().id
                    else:
                        mostrar_resumo_estacao = True
                        estacao_concluida_url = reverse(
                            "exercicios:estacao_concluida", args=[estacao_atual.id]
                        )

                # Recalcula o progresso após a resposta para enviar o valor atualizado
                (
                    progresso_percentual,
                    exercicios_concluidos_count,
                    total_exercicios_modulo,
                ) = mecanicas_services.calcular_progresso_estacao(
                    exercicio.estacao, request.user
                )
                total_exercicios_estacao = (
                    resumo_estacao["total_exercicios"]
                    or Exercicio.objects.filter(estacao=exercicio.estacao).count()
                )
                porcentagem_acertos = (
                    int((resumo_estacao["acertos"] / total_exercicios_estacao) * 100)
                    if total_exercicios_estacao
                    else 0
                )

                # Monta o dicionário de dados para a resposta JSON
                data = {
                    "resultado": resultado,  # 'correto' ou 'incorreto'
                    "correta": correta,
                    "resposta_submetida": resposta_usuario,
                    "proximo_exercicio_id": proximo_exercicio_id,
                    "estacao_concluida_url": estacao_concluida_url,  # Será null se a estação não terminou
                    "vidas_atuais": perfil.vidas_atuais,
                    "sem_vidas": perfil.vidas_atuais <= 0,
                    "progresso": {
                        "percentual": progresso_percentual,
                        "concluidos": exercicios_concluidos_count,
                        "total": total_exercicios_modulo,
                    },
                    "resposta_correta": (
                        exercicio.resposta_correta
                        if exercicio.tipo == "mcq"
                        else (
                            exercicio.resposta_vf_correta
                            if exercicio.tipo == "vf"
                            else (
                                exercicio.resposta_texto_codigo
                                if exercicio.tipo == "lacuna"
                                else None
                            )
                        )
                    ),
                    "resumo_estacao": {
                        "mostrar": mostrar_resumo_estacao,
                        "acertos": resumo_estacao["acertos"],
                        "erros": resumo_estacao["erros"],
                        "xp_ganho": resumo_estacao["xp_ganho"],
                        "porcentagem_acertos": porcentagem_acertos,
                        "total_exercicios": total_exercicios_estacao,
                        "continuar_url": reverse(
                            "exercicios:percurso", args=[exercicio.modulo.id]
                        ),
                    },
                    "conquistas_novas": serializar_conquistas_novas(conquistas_novas),
                }
                return JsonResponse(data)

            # Se NÃO for AJAX, o código continua como antes, para o caso de o JS falhar.
            # O código abaixo só será executado se a requisição for um POST normal.
            resposta_submetida = resposta_usuario
            proximo_exercicio_id_para_continuar = None
            if correta:
                estacao_atual = exercicio.estacao
                exercicios_livres_restantes = (
                    mecanicas_services.obter_exercicios_nao_concluidos(
                        estacao_atual, request.user
                    ).order_by("id")
                )
                if exercicios_livres_restantes.exists():
                    proximo_exercicio_id_para_continuar = (
                        exercicios_livres_restantes.first().id
                    )
                else:
                    return redirect(
                        "exercicios:estacao_concluida", estacao_id=estacao_atual.id
                    )

    # Prepara o código com a marcação da lacuna antes de renderizar o template.
    codigo_renderizado = None
    if exercicio.tipo == "lacuna" and exercicio.codigo:
        marcador = _marcador_lacuna(exercicio, resposta_submetida)
        codigo_renderizado = mark_safe(
            escape(exercicio.codigo).replace("__LACUNA__", marcador)
        )

    # Nova lógica para decidir se o modal de saída deve ser mostrado
    mostrar_modal_confirmacao_saida = progresso_percentual > 0

    # Verificar se o usuário não tem mais vidas
    sem_vidas = perfil.vidas_atuais <= 0

    context = {
        "exercicio": exercicio,
        "resultado": resultado,
        "correta": correta,
        "perfil": perfil,
        "modulo_id": exercicio.modulo.id,
        "alternativas": alternativas,
        "resposta_submetida": resposta_submetida,  # Passa a resposta do usuário para o template
        "proximo_exercicio_id_para_continuar": proximo_exercicio_id_para_continuar,  # Ainda útil para o botão continuar normal
        "sem_vidas": sem_vidas,
        "progresso_percentual": progresso_percentual,
        "exercicios_concluidos_count": exercicios_concluidos_count,
        "total_exercicios_modulo": total_exercicios_modulo,
        "mostrar_modal_confirmacao_saida": mostrar_modal_confirmacao_saida,  # Adicionamos aqui
        "exercicios_pendentes": exercicios_pendentes,  # Adiciona a variável ao contexto
        "codigo_renderizado": codigo_renderizado,
        "conquistas_novas": serializar_conquistas_novas(conquistas_novas),
    }

    return render(request, "exercicios/resolver_exercicio.html", context)


@login_required
@require_POST
def reportar_problema(request, exercicio_id):
    exercicio = get_object_or_404(Exercicio, id=exercicio_id)
    motivo = request.POST.get("motivo")
    motivos_validos = {valor for valor, _ in ReporteExercicio.MOTIVO_CHOICES}

    if motivo not in motivos_validos:
        return redirect("exercicios:resolver_exercicio", exercicio_id=exercicio.id)

    ReporteExercicio.objects.create(
        exercicio=exercicio,
        usuario=request.user,
        motivo=motivo,
    )
    return redirect(f"{reverse('exercicios:resolver_exercicio', args=[exercicio.id])}?reportado=1")


@login_required
def iniciar_exercicios(request, exercicio_id):
    exercicio = get_object_or_404(Exercicio, id=exercicio_id)
    if (
        mecanicas_services.obter_status_estacao(exercicio.estacao, request.user)
        == "bloqueado"
    ):
        raise PermissionDenied("Esta estação ainda está bloqueada.")
    limpar_ordens_alternativas_da_estacao(request, exercicio.estacao)
    mecanicas_services.reiniciar_estacao(exercicio.estacao, request.user)
    resumo_estacoes = request.session.setdefault("resumo_estacoes", {})
    resumo_estacoes[str(exercicio.estacao_id)] = {
        "acertos": 0,
        "erros": 0,
        "xp_ganho": 0,
        "total_exercicios": Exercicio.objects.filter(
            estacao_id=exercicio.estacao_id
        ).count(),
    }
    request.session["resumo_estacoes"] = resumo_estacoes
    request.session["estacao_resumo_atual_id"] = str(exercicio.estacao_id)
    return redirect("exercicios:resolver_exercicio", exercicio_id=exercicio.id)


@login_required
def estacao_concluida_view(request, estacao_id):
    estacao = get_object_or_404(Estacao, id=estacao_id)
    perfil = get_or_create_perfil(request.user)

    total_xp_estacao = (
        Exercicio.objects.filter(estacao=estacao).aggregate(total_xp=Sum("xp"))[
            "total_xp"
        ]
        or 0
    )

    resumo_estacao = request.session.get("resumo_estacoes", {}).get(str(estacao.id), {})
    total_exercicios_estacao = Exercicio.objects.filter(estacao=estacao).count()
    exercicios_concluidos = ExercicioUsuario.objects.filter(
        usuario=request.user, exercicio__estacao=estacao, status="concluido"
    ).count()
    acertos = min(exercicios_concluidos, total_exercicios_estacao)
    erros = resumo_estacao.get("erros", 0)
    xp_ganho = total_xp_estacao if acertos == total_exercicios_estacao else 0
    porcentagem_acertos = (
        int((acertos / total_exercicios_estacao) * 100)
        if total_exercicios_estacao
        else 0
    )

    context = {
        "estacao": estacao,
        "total_xp_estacao": total_xp_estacao,
        "perfil": perfil,
        "modulo_id": estacao.secao.modulo.id,
        "resumo_estacao": {
            "acertos": acertos,
            "erros": erros,
            "xp_ganho": xp_ganho,
            "porcentagem_acertos": porcentagem_acertos,
            "total_exercicios": total_exercicios_estacao,
        },
    }
    return render(request, "exercicios/estacao_concluida.html", context)


@login_required
def get_exercicio_data(request, exercicio_id):
    """
    Endpoint de API que retorna os dados de um exercício em JSON
    para serem usados pelo frontend.
    """
    exercicio = get_object_or_404(Exercicio, id=exercicio_id)
    if (
        mecanicas_services.obter_status_estacao(exercicio.estacao, request.user)
        == "bloqueado"
    ):
        raise PermissionDenied("Esta estação ainda está bloqueada.")

    # Aqui você pode customizar exatamente quais dados quer enviar
    # para reconstruir a tela do exercício.
    data = {
        "id": exercicio.id,
        "tipo": exercicio.tipo,
        "enunciado": linebreaksbr(exercicio.enunciado) if exercicio.enunciado else "",
        "codigo": exercicio.codigo if exercicio.codigo else "",
        "imagem_url": exercicio.imagem.url if exercicio.imagem else None,
        # Obtém as alternativas como uma lista de tuplas (numero, texto)
        "alternativas": (
            obter_alternativas(exercicio, request) if exercicio.tipo == "mcq" else []
        ),
        "url_resolucao": reverse("exercicios:resolver_exercicio", args=[exercicio.id]),
    }

    if exercicio.tipo == "lacuna" and exercicio.codigo:
        tamanho_lacuna = max(1, len((exercicio.resposta_texto_codigo or "").strip()))
        data["tamanho_lacuna"] = tamanho_lacuna
        data["codigo_renderizado"] = escape(exercicio.codigo).replace(
            "__LACUNA__",
            _marcador_lacuna(exercicio),
        )
    else:
        data["codigo_renderizado"] = data["codigo"]

    if exercicio.tipo == "info":
        perfil = get_or_create_perfil(request.user)
        if (
            perfil
            and mecanicas_services.obter_status_exercicio(exercicio, request.user)
            == "livre"
        ):
            conquistas_novas = mecanicas_services.marcar_exercicio_concluido(
                exercicio, perfil, request.user
            )
            data["conquistas_novas"] = serializar_conquistas_novas(conquistas_novas)

        proximo_exercicio_livre = (
            mecanicas_services.obter_exercicios_nao_concluidos(
                exercicio.estacao, request.user
            )
            .exclude(id=exercicio.id)
            .order_by("id")
            .first()
        )
        data["proximo_exercicio_id"] = (
            proximo_exercicio_livre.id if proximo_exercicio_livre else None
        )

    return JsonResponse(data)
