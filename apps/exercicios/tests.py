import json

from django.test import TestCase
from django.urls import reverse

from apps.exercicios.models import (
    Estacao,
    Exercicio,
    ExercicioUsuario,
    Modulo,
    ReporteExercicio,
    Secao,
)
from apps.usuarios.models import Divisao, Perfil
from django.contrib.auth import get_user_model


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
        self.assertContains(resposta_final, "⚡ 17")
        self.assertContains(resposta_final, "100%")


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

    def test_secao_so_desbloqueia_ao_concluir_todas_as_cinco_estacoes(self):
        self.client.force_login(self.user)
        self.concluir_estacoes(0, 4)

        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))
        self.assertContains(response, "Introdução")
        self.assertContains(response, "While")
        self.assertNotContains(response, 'class="section-title">While</h1>')

        self.concluir_estacoes(0, 1, inicio=4)
        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))
        self.assertContains(response, 'class="section-title">While</h1>')
        self.assertContains(response, "Do-while")
        self.assertNotContains(response, ">For<", html=False)

        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))
        self.assertContains(response, 'class="section-title">While</h1>')

    def test_desbloqueio_e_por_usuario_e_bloqueia_acesso_direto(self):
        self.concluir_estacoes(0, 5)
        exercicio_while = self.estacoes[1][0][1]

        self.client.force_login(self.outro_usuario)
        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))
        self.assertContains(response, "Introdução")
        self.assertNotContains(response, 'class="section-title">While</h1>')
        self.assertEqual(
            self.client.get(
                reverse("exercicios:iniciar_estacao", args=[exercicio_while.id])
            ).status_code,
            403,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("exercicios:percurso", args=[self.modulo.id]))
        self.assertContains(response, 'class="section-title">While</h1>')

    def test_mapa_exibe_todas_as_secoes_sem_desbloquear_as_bloqueadas(self):
        self.client.force_login(self.user)
        self.concluir_estacoes(0, 5)

        response = self.client.get(
            reverse("exercicios:percurso", args=[self.modulo.id]),
            {"visualizacao": "todas"},
        )

        self.assertContains(response, "Todas as seções")
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
