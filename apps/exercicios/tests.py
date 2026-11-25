import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.urls import reverse

from apps.exercicios.models import (
    Estacao,
    BauEstacaoUsuario,
    Exercicio,
    ExercicioUsuario,
    Modulo,
    ReporteExercicio,
    Secao,
)
from apps.usuarios.models import Divisao, Perfil
from django.contrib.auth import get_user_model
from apps.mecanicas_jogo import services as mecanicas_services
from apps.exercicios.views import _renderizar_codigo_ide, _renderizar_codigo_leitura
from apps.exercicios.admin import ExercicioAdminForm


class BlocoCodigoTests(SimpleTestCase):
    def test_codigo_de_leitura_tem_linhas_realce_e_html_escapado(self):
        html = str(_renderizar_codigo_leitura('int i = 0;\n// <script>alert(1)</script>'))

        self.assertIn('class="ide-code__numero">1</span>', html)
        self.assertIn('class="ide-code__numero">2</span>', html)
        self.assertIn('class="demo-token-palavra">int</span>', html)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_lacuna_permanece_editavel_sem_expor_resposta(self):
        exercicio = Exercicio(codigo='int i = __LACUNA__;', resposta_texto_codigo='42')
        html = str(_renderizar_codigo_ide(exercicio))

        self.assertIn('class="lacuna-marker"', html)
        self.assertIn('class="ide-code__numero">1</span>', html)
        self.assertNotIn('value="42"', html)

    def test_marcador_legado_de_tres_sublinhados_vira_campo(self):
        exercicio = Exercicio(codigo='while (contador ___ 4) {', resposta_texto_codigo='<')
        html = str(_renderizar_codigo_ide(exercicio))

        self.assertEqual(html.count('class="lacuna-marker"'), 1)
        self.assertNotIn('___', html)
        self.assertNotIn('value="&lt;"', html)

    def test_resposta_vazia_nao_acerta_questao_sem_gabarito(self):
        exercicio = Exercicio(tipo="mcq", resposta_correta=None)
        self.assertFalse(mecanicas_services.verificar_resposta(exercicio, None))

    def test_ponto_e_virgula_isolado_e_resposta_valida_da_lacuna(self):
        exercicio = Exercicio(tipo="lacuna", resposta_texto_codigo=";")
        self.assertTrue(mecanicas_services.verificar_resposta(exercicio, ";"))
        self.assertFalse(mecanicas_services.verificar_resposta(exercicio, ""))
        self.assertFalse(mecanicas_services.verificar_resposta(exercicio, "outro"))


@skipUnless(connection.vendor == "postgresql", "Bloqueio de linha exige PostgreSQL")
class ConcessaoXpConcorrenteTests(TransactionTestCase):
    def test_duas_respostas_simultaneas_concedem_xp_uma_vez(self):
        usuario = get_user_model().objects.create_user(username="aluno-concorrente")
        Perfil.objects.create(user=usuario)
        modulo = Modulo.objects.create(nome="Loops", descricao="Teste")
        secao = Secao.objects.create(nome="Introdução", modulo=modulo)
        estacao = Estacao.objects.create(nome="Estação", secao=secao)
        exercicio = Exercicio.objects.create(
            modulo=modulo, estacao=estacao, tipo="mcq", xp=20,
            resposta_correta="1",
        )
        largada = Barrier(2)

        def responder():
            close_old_connections()
            try:
                perfil = Perfil.objects.get(user=usuario)
                largada.wait(timeout=10)
                mecanicas_services.atualizar_estado_do_perfil_e_exercicio(
                    perfil, exercicio, usuario, correta=True
                )
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = [executor.submit(responder) for _ in range(2)]
            for resultado in resultados:
                resultado.result(timeout=20)

        progresso = ExercicioUsuario.objects.get(usuario=usuario, exercicio=exercicio)
        self.assertTrue(progresso.xp_concedido)
        self.assertEqual(Perfil.objects.get(user=usuario).xp, 20)

    def test_duas_respostas_erradas_na_ultima_vida_descontam_uma_vez(self):
        usuario = get_user_model().objects.create_user(username="aluno-ultima-vida")
        Perfil.objects.create(user=usuario, vidas_atuais=1)
        modulo = Modulo.objects.create(nome="Loops", descricao="Teste")
        secao = Secao.objects.create(nome="Introdução", modulo=modulo)
        estacao = Estacao.objects.create(nome="Estação", secao=secao)
        exercicio = Exercicio.objects.create(
            modulo=modulo, estacao=estacao, tipo="mcq", resposta_correta="2",
        )
        largada = Barrier(2)

        def responder():
            close_old_connections()
            try:
                perfil = Perfil.objects.get(user=usuario)
                largada.wait(timeout=10)
                try:
                    mecanicas_services.processar_resposta_exercicio(
                        "1", exercicio, perfil, usuario
                    )
                    return "processada"
                except mecanicas_services.SemVidas:
                    return "sem_vidas"
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = [executor.submit(responder) for _ in range(2)]
            estados = [resultado.result(timeout=20) for resultado in resultados]

        self.assertCountEqual(estados, ["processada", "sem_vidas"])
        perfil = Perfil.objects.get(user=usuario)
        self.assertEqual(perfil.vidas_atuais, 0)
        self.assertEqual(perfil.xp, 0)


class ReporteExercicioTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="aluno-reporte", password="senha123"
        )
        modulo = Modulo.objects.create(nome="Loops", descricao="Desc", ordem=1)
        secao = Secao.objects.create(nome="For", modulo=modulo, ordem=1)
        estacao = Estacao.objects.create(nome="Estação", secao=secao)
        self.exercicio = Exercicio.objects.create(
            modulo=modulo,
            estacao=estacao,
            titulo="Exercício para reportar",
            tipo="mcq",
            resposta_correta="1",
        )

    def test_cria_reporte_pendente_com_exercicio_usuario_e_motivo(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("exercicios:reportar_problema", args=[self.exercicio.id]),
            {"motivo": "resposta_incorreta"},
        )

        self.assertRedirects(
            response,
            f"{reverse('exercicios:resolver_exercicio', args=[self.exercicio.id])}?reportado=1",
        )
        reporte = ReporteExercicio.objects.get()
        self.assertEqual(reporte.exercicio, self.exercicio)
        self.assertEqual(reporte.usuario, self.user)
        self.assertEqual(reporte.motivo, "resposta_incorreta")
        self.assertEqual(reporte.status, "pendente")
        self.assertIsNotNone(reporte.criado_em)


class ResolverExercicioResumoEstacaoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="aluno",
            email="aluno@example.com",
            password="senha123",
        )
        self.divisao, _ = Divisao.objects.get_or_create(nome="Bronze")
        self.perfil = Perfil.objects.create(user=self.user)
        self.perfil.divisao = self.divisao
        self.perfil.save(update_fields=["divisao"])

        self.modulo = Modulo.objects.create(
            nome="Módulo Teste", descricao="Desc", ordem=1
        )
        self.secao = Secao.objects.create(
            nome="Seção Teste", modulo=self.modulo, ordem=1
        )
        self.estacao = Estacao.objects.create(nome="Estação Teste", secao=self.secao)

        self.exercicio_1 = Exercicio.objects.create(
            modulo=self.modulo,
            estacao=self.estacao,
            titulo="Exercício 1",
            enunciado="Pergunta 1",
            tipo="mcq",
            xp=10,
            alternativa_1="A",
            alternativa_2="B",
            alternativa_3="C",
            alternativa_4="D",
            resposta_correta="2",
        )
        self.exercicio_2 = Exercicio.objects.create(
            modulo=self.modulo,
            estacao=self.estacao,
            titulo="Exercício 2",
            enunciado="Pergunta 2",
            tipo="mcq",
            xp=20,
            alternativa_1="A",
            alternativa_2="B",
            alternativa_3="C",
            alternativa_4="D",
            resposta_correta="3",
        )

    def test_codigo_da_multipla_escolha_usa_editor_compartilhado(self):
        self.exercicio_1.codigo = 'int i = 0;\nprintf("oi");'
        self.exercicio_1.save(update_fields=["codigo"])
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("exercicios:resolver_exercicio", args=[self.exercicio_1.id])
        )

        self.assertContains(response, 'class="ide-editor"')
        self.assertContains(response, 'class="ide-code__numero">2</span>')
        self.assertContains(response, 'class="demo-token-funcao">printf</span>')

    def test_lacuna_legada_aparece_editavel_na_pagina_e_na_api(self):
        exercicio = Exercicio.objects.create(
            modulo=self.modulo,
            estacao=self.estacao,
            tipo="lacuna",
            codigo="while (contador ___ 4) {\n    contador++;\n}",
            resposta_texto_codigo="<",
        )
        self.client.force_login(self.user)

        pagina = self.client.get(reverse("exercicios:resolver_exercicio", args=[exercicio.id]))
        api = self.client.get(reverse("exercicios:api_get_exercicio_data", args=[exercicio.id]))

        self.assertContains(pagina, 'class="lacuna-marker"')
        self.assertContains(pagina, "Clique no campo destacado")
        self.assertIn('class="lacuna-marker"', api.json()["codigo_renderizado"])
        self.assertNotIn("___", api.json()["codigo_renderizado"])

    def test_admin_rejeita_lacuna_sem_marcador(self):
        form = ExercicioAdminForm(data={
            "modulo": self.modulo.id,
            "estacao": self.estacao.id,
            "tipo": "lacuna",
            "codigo": "while (contador < 4) {}",
            "respostas_aceitas": "<",
            "xp": 10,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("codigo", form.errors)

    def test_resposta_incorreta_ajax_nao_revela_gabarito(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("exercicios:resolver_exercicio", args=[self.exercicio_1.id]),
            {"acao": "responder", "is_ajax_request": "1", "resposta": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["correta"])
        self.assertNotIn("resposta_correta", response.json())

    def test_resposta_incorreta_no_html_nao_destaca_gabarito(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("exercicios:resolver_exercicio", args=[self.exercicio_1.id]),
            {"acao": "responder", "resposta": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "alternativa-correta")

    def test_sem_vidas_rejeita_resposta_correta_sem_conceder_xp(self):
        self.perfil.vidas_atuais = 0
        self.perfil.save(update_fields=["vidas_atuais"])
        self.client.force_login(self.user)
        url = reverse("exercicios:resolver_exercicio", args=[self.exercicio_1.id])

        response = self.client.post(
            url,
            {"acao": "responder", "is_ajax_request": "1", "resposta": "2"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["erro"], "sem_vidas")
        self.assertFalse(ExercicioUsuario.objects.filter(usuario=self.user).exists())
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.xp, 0)

        response_normal = self.client.post(url, {"acao": "responder", "resposta": "2"}, follow=True)
        self.assertContains(response_normal, "Você está sem vidas")
        self.assertEqual(self.perfil.xp, 0)

    def test_resumo_da_estacao_eh_enviado_no_ajax_quando_a_estacao_termina(self):
        self.client.force_login(self.user)

        response_incorreta = self.client.post(
            reverse("exercicios:resolver_exercicio", args=[self.exercicio_1.id]),
            {"acao": "responder", "is_ajax_request": "1", "resposta": "1"},
            follow=False,
        )
        self.assertEqual(response_incorreta.status_code, 200)

        response_final = self.client.post(
            reverse("exercicios:resolver_exercicio", args=[self.exercicio_2.id]),
            {"acao": "responder", "is_ajax_request": "1", "resposta": "3"},
            follow=False,
        )
        self.assertEqual(response_final.status_code, 200)

        data = json.loads(response_final.content)

        self.assertTrue(data["resumo_estacao"]["mostrar"])
        self.assertEqual(data["resumo_estacao"]["acertos"], 1)
        self.assertEqual(data["resumo_estacao"]["erros"], 1)
        self.assertEqual(data["resumo_estacao"]["xp_ganho"], 20)
        self.assertEqual(data["resumo_estacao"]["porcentagem_acertos"], 50)
        self.assertEqual(data["resumo_estacao"]["total_exercicios"], 2)


    def test_concluir_estacao_completa_registra_ofensiva(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse("exercicios:resolver_exercicio", args=[self.exercicio_1.id]),
            {"acao": "responder", "is_ajax_request": "1", "resposta": "2"},
        )
        response = self.client.post(
            reverse("exercicios:resolver_exercicio", args=[self.exercicio_2.id]),
            {"acao": "responder", "is_ajax_request": "1", "resposta": "3"},
        )

        data = json.loads(response.content)
        self.client.get(data["estacao_concluida_url"])
        self.perfil.refresh_from_db()

        self.assertEqual(self.perfil.sequencia_dias, 1)

    def test_tempo_da_estacao_para_no_ultimo_exercicio_correto(self):
        self.client.force_login(self.user)
        self.client.get(reverse("exercicios:iniciar_estacao", args=[self.exercicio_1.id]))

        self.client.post(
            reverse("exercicios:resolver_exercicio", args=[self.exercicio_1.id]),
            {"acao": "responder", "is_ajax_request": "1", "resposta": "2"},
        )
        self.client.post(
            reverse("exercicios:resolver_exercicio", args=[self.exercicio_2.id]),
            {"acao": "responder", "is_ajax_request": "1", "resposta": "3"},
        )

        tentativa = self.estacao.tentativas.get(usuario=self.user)
        self.assertIsNotNone(tentativa.concluida_em)
        self.assertIsNotNone(tentativa.duracao_segundos)


class ResumoExercicioInformativoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="aluno-info", password="senha123"
        )
        Perfil.objects.create(user=self.user)
        modulo = Modulo.objects.create(nome="Módulo Info", descricao="Desc", ordem=1)
        secao = Secao.objects.create(nome="Seção Info", modulo=modulo, ordem=1)
        estacao = Estacao.objects.create(nome="Estação Info", secao=secao)
        self.exercicio_info = Exercicio.objects.create(
            modulo=modulo,
            estacao=estacao,
            titulo="Leia isto",
            tipo="info",
            xp=10,
        )
        self.exercicio_multipla_escolha = Exercicio.objects.create(
            modulo=modulo,
            estacao=estacao,
            titulo="Responda isto",
            tipo="mcq",
            xp=7,
            alternativa_1="Certa",
            alternativa_2="Errada",
            resposta_correta="1",
        )

    def test_aula_de_repeticao_exibe_conceitos_codigo_e_fluxo(self):
        self.exercicio_info.enunciado = (
            "Uma estrutura de repetição normalmente possui: "
            "Inicialização, Condição e Atualização."
        )
        self.exercicio_info.save(update_fields=["enunciado"])
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("exercicios:resolver_exercicio", args=[self.exercicio_info.id])
        )

        self.assertContains(response, "Como um laço funciona?")
        self.assertContains(response, "while")
        self.assertContains(response, "Cuidado com o loop infinito!")
        self.assertContains(response, "info_repeticao.js")
        self.assertContains(response, "Continuar")

    def test_exercicio_informativo_entra_no_resumo_da_estacao(self):
        self.client.force_login(self.user)

        self.client.get(
            reverse("exercicios:resolver_exercicio", args=[self.exercicio_info.id])
        )
        response = self.client.post(
            reverse(
                "exercicios:resolver_exercicio",
                args=[self.exercicio_multipla_escolha.id],
            ),
            {"acao": "responder", "is_ajax_request": "1", "resposta": "1"},
        )

        data = json.loads(response.content)
        self.assertTrue(data["resumo_estacao"]["mostrar"])
        self.assertEqual(data["resumo_estacao"]["acertos"], 2)
        self.assertEqual(data["resumo_estacao"]["xp_ganho"], 17)
        self.assertEqual(data["resumo_estacao"]["porcentagem_acertos"], 100)

        resposta_final = self.client.get(
            reverse("exercicios:estacao_concluida", args=[self.exercicio_info.estacao_id])
        )
        self.assertContains(resposta_final, "17 XP")
        self.assertContains(resposta_final, "100%")

    def test_ultimo_exercicio_informativo_leva_para_conclusao_da_estacao(self):
        self.client.force_login(self.user)
        self.exercicio_multipla_escolha.delete()

        response = self.client.get(
            reverse("exercicios:resolver_exercicio", args=[self.exercicio_info.id])
        )

        url_conclusao = reverse(
            "exercicios:estacao_concluida", args=[self.exercicio_info.estacao_id]
        )
        self.assertContains(response, url_conclusao)
        self.assertTrue(
            ExercicioUsuario.objects.filter(
                usuario=self.user,
                exercicio=self.exercicio_info,
                status="concluido",
            ).exists()
        )


class BauEstacaoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="aluno-bau", password="senha123"
        )
        self.perfil = Perfil.objects.create(user=self.user)
        self.modulo = Modulo.objects.create(nome="Módulo Baú", descricao="Desc", ordem=1)
        self.secao = Secao.objects.create(nome="Seção Baú", modulo=self.modulo, ordem=1)
        self.estacoes = []
        for numero in range(1, 4):
            estacao = Estacao.objects.create(
                nome=f"Estação {numero}", secao=self.secao
            )
            exercicio = Exercicio.objects.create(
                modulo=self.modulo,
                estacao=estacao,
                titulo=f"Exercício {numero}",
                tipo="mcq",
                resposta_correta="1",
            )
            self.estacoes.append((estacao, exercicio))

    def test_bau_desbloqueia_apos_segunda_estacao_e_libera_terceira_ao_coletar(self):
        self.client.force_login(self.user)
        for _, exercicio in self.estacoes[:2]:
            ExercicioUsuario.objects.create(
                usuario=self.user, exercicio=exercicio, status="concluido"
            )

        response = self.client.get(
            reverse("exercicios:percurso", args=[self.modulo.id])
        )
        self.assertContains(response, "Baú desbloqueado!")

        response = self.client.post(
            reverse("exercicios:coletar_bau_estacao", args=[self.secao.id])
        )
        self.assertRedirects(
            response,
            f"{reverse('exercicios:percurso', args=[self.modulo.id])}?bau_coletado=1",
        )
        self.assertTrue(
            BauEstacaoUsuario.objects.filter(usuario=self.user, secao=self.secao).exists()
        )
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.cristal, 5)
        self.assertEqual(self.perfil.xp, 25)
        self.assertEqual(
            mecanicas_services.obter_status_estacao(self.estacoes[2][0], self.user),
            "livre",
        )


class PercursoPorSecaoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="aluno-percurso", password="senha123"
        )
        self.outro_usuario = get_user_model().objects.create_user(
            username="outro-aluno", password="senha123"
        )
        self.modulo = Modulo.objects.create(nome="Loops", descricao="Desc", ordem=1)
        self.secoes = [
            Secao.objects.create(nome=nome, modulo=self.modulo, ordem=ordem)
            for ordem, nome in enumerate(["Introdução", "While", "Do-while", "For"], 1)
        ]
        self.estacoes = []
        for secao in self.secoes:
            estacoes_secao = []
            for numero in range(1, 6):
                estacao = Estacao.objects.create(nome=f"Estação {numero}", secao=secao)
                exercicio = Exercicio.objects.create(
                    modulo=self.modulo,
                    estacao=estacao,
                    titulo=f"Exercício {secao.nome} {numero}",
                    tipo="mcq",
                    resposta_correta="1",
                )
                estacoes_secao.append((estacao, exercicio))
            self.estacoes.append(estacoes_secao)

    def concluir_estacoes(self, indice_secao, quantidade, inicio=0):
        for _, exercicio in self.estacoes[indice_secao][inicio : inicio + quantidade]:
            ExercicioUsuario.objects.create(
                usuario=self.user, exercicio=exercicio, status="concluido"
            )

    def test_ultima_estacao_livre_tem_acionador_e_link_para_comecar(self):
        self.client.force_login(self.user)
        self.concluir_estacoes(0, 4)
        BauEstacaoUsuario.objects.create(usuario=self.user, secao=self.secoes[0])
        ultima_estacao, ultimo_exercicio = self.estacoes[0][4]

        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))

        self.assertContains(response, f'aria-controls="dropdown-{ultima_estacao.id}"')
        self.assertContains(response, 'aria-label="Abrir estação Estação 5"')
        self.assertContains(
            response, reverse("exercicios:iniciar_estacao", args=[ultimo_exercicio.id])
        )

    def test_exibe_somente_secao_atual_e_proxima_bloqueada(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))

        self.assertContains(response, "Introdução")
        self.assertContains(response, "While")
        self.assertContains(response, "Seção bloqueada")
        self.assertNotContains(response, "Do-while")
        self.assertNotContains(response, ">For<", html=False)

    def test_primeiro_acesso_exibe_uma_estacao_livre_e_as_demais_bloqueadas(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))

        self.assertContains(response, "status-livre", count=1)
        self.assertContains(response, "status-bloqueado", count=4)
        self.assertNotContains(response, "status-default")
        self.assertContains(response, "station-circle--animada", count=1)

    def test_secao_so_desbloqueia_ao_concluir_todas_as_cinco_estacoes(self):
        self.client.force_login(self.user)
        self.concluir_estacoes(0, 4)

        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))
        self.assertContains(response, "Introdução")
        self.assertContains(response, "While")
        self.assertContains(response, 'class="percurso-navegacao__secao">Loops / Introdução</span>')

        self.concluir_estacoes(0, 1, inicio=4)
        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))
        self.assertContains(response, 'class="percurso-navegacao__secao">Loops / While</span>')
        self.assertContains(response, "Do-while")
        self.assertNotContains(response, ">For<", html=False)

        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))
        self.assertContains(response, 'class="percurso-navegacao__secao">Loops / While</span>')

    def test_desbloqueio_e_por_usuario_e_bloqueia_acesso_direto(self):
        self.concluir_estacoes(0, 5)
        exercicio_while = self.estacoes[1][0][1]

        self.client.force_login(self.outro_usuario)
        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))
        self.assertContains(response, "Introdução")
        self.assertContains(response, 'class="percurso-navegacao__secao">Loops / Introdução</span>')
        self.assertEqual(
            self.client.get(
                reverse("exercicios:iniciar_estacao", args=[exercicio_while.id])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("exercicios:estacao_concluida", args=[self.estacoes[1][0][0].id])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse("exercicios:reportar_problema", args=[exercicio_while.id]),
                {"motivo": "resposta_incorreta"},
            ).status_code,
            403,
        )
        self.assertFalse(ReporteExercicio.objects.exists())

        self.client.force_login(self.user)
        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))
        self.assertContains(response, 'class="percurso-navegacao__secao">Loops / While</span>')

    def test_mapa_exibe_todas_as_secoes_sem_desbloquear_as_bloqueadas(self):
        self.client.force_login(self.user)
        self.concluir_estacoes(0, 5)

        response = self.client.get(
            reverse("exercicios:percurso", args=[self.modulo.id]),
            {"visualizacao": "todas"},
        )

        self.assertContains(response, "Percurso principal")
        self.assertContains(response, 'data-estado="concluida"')
        self.assertContains(response, 'data-estado="atual"')
        self.assertContains(response, 'data-estado="bloqueada"')
        self.assertContains(response, "Introdução")
        self.assertContains(response, "While")
        self.assertContains(response, "Do-while")
        self.assertContains(response, "For")
        self.assertContains(response, "5 de 5 estações concluídas")
        self.assertContains(response, "100%")
        self.assertContains(response, ">Continuar<", html=False)

    def test_secao_concluida_pode_ser_revisitada_pelo_mapa(self):
        self.client.force_login(self.user)
        self.concluir_estacoes(0, 5)
        url = reverse("exercicios:percurso", args=[self.modulo.id])

        mapa = self.client.get(url, {"visualizacao": "todas"})
        self.assertContains(mapa, f"?secao={self.secoes[0].id}")
        self.assertContains(mapa, 'aria-label="Revisar seção Introdução"')

        revisao = self.client.get(url, {"secao": self.secoes[0].id})
        self.assertContains(
            revisao,
            'class="percurso-navegacao__secao">Loops / Introdução</span>',
        )
        self.assertContains(revisao, "status-completado", count=5)
        self.assertContains(revisao, "Praticar Novamente", count=5)

    def test_secoes_bloqueadas_nao_podem_ser_abertas_pelo_parametro(self):
        self.client.force_login(self.user)
        url = reverse("exercicios:percurso", args=[self.modulo.id])

        self.assertEqual(
            self.client.get(url, {"secao": self.secoes[1].id}).status_code,
            403,
        )
        self.assertEqual(self.client.get(url, {"secao": 999999}).status_code, 404)
