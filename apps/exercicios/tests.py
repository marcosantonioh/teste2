import json

from django.test import TestCase
from django.urls import reverse

from apps.exercicios.models import Estacao, Exercicio, Modulo, Secao
from apps.usuarios.models import Divisao, Perfil
from django.contrib.auth import get_user_model


class ResolverExercicioResumoEstacaoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="aluno",
            email="aluno@example.com",
            password="senha123",
        )
        self.divisao = Divisao.objects.create(nome="Bronze", ordem=1)
        self.perfil = Perfil.objects.get(user=self.user)
        self.perfil.divisao = self.divisao
        self.perfil.save(update_fields=["divisao"])

        self.modulo = Modulo.objects.create(
            nome="Módulo Teste", descricao="Desc", ordem=1
        )
        self.secao = Secao.objects.create(
            nome="Seção Teste", modulo=self.modulo, ordem=1
        )
        self.estacao = Estacao.objects.create(
            nome="Estação Teste", secao=self.secao, status="livre"
        )

        self.exercicio_1 = Exercicio.objects.create(
            modulo=self.modulo,
            estacao=self.estacao,
            titulo="Exercício 1",
            enunciado="Pergunta 1",
            tipo="mcq",
            status="livre",
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
            status="livre",
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
