import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.exercicios.models import Estacao, Exercicio, Modulo, Secao
from apps.usuarios.models import Perfil

from .services import atualizar_estado_do_perfil_e_exercicio


class OfensivaPorEstacaoTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="aluno-ofensiva", password="senha-segura"
        )
        self.perfil = Perfil.objects.create(user=self.usuario)
        modulo = Modulo.objects.create(nome="Lógica", descricao="Base")
        secao = Secao.objects.create(modulo=modulo, nome="Início")
        self.estacao = Estacao.objects.create(secao=secao, nome="Estação 1")
        self.exercicio_1 = Exercicio.objects.create(
            modulo=modulo, estacao=self.estacao, tipo="mcq", resposta_correta="1"
        )
        self.exercicio_2 = Exercicio.objects.create(
            modulo=modulo, estacao=self.estacao, tipo="mcq", resposta_correta="1"
        )

    def test_ofensiva_so_aumenta_quando_estacao_inteira_eh_concluida(self):
        atualizar_estado_do_perfil_e_exercicio(
            self.perfil, self.exercicio_1, self.usuario, correta=True
        )
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.sequencia_dias, 0)

        atualizar_estado_do_perfil_e_exercicio(
            self.perfil, self.exercicio_2, self.usuario, correta=True
        )
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.sequencia_dias, 1)
        self.assertEqual(
            self.perfil.ultima_estacao_ofensiva,
            Perfil._data_atual_ofensiva(),
        )

    def test_ofensiva_conta_uma_vez_por_dia_e_reinicia_apos_intervalo(self):
        hoje = Perfil._data_atual_ofensiva()
        self.assertTrue(self.perfil.registrar_estacao_concluida(hoje))
        self.assertFalse(self.perfil.registrar_estacao_concluida(hoje))
        self.assertTrue(
            self.perfil.registrar_estacao_concluida(hoje + datetime.timedelta(days=1))
        )
        self.assertEqual(self.perfil.sequencia_dias, 2)

        self.assertTrue(
            self.perfil.registrar_estacao_concluida(hoje + datetime.timedelta(days=3))
        )
        self.assertEqual(self.perfil.sequencia_dias, 1)
