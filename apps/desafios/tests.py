from django.contrib.auth.models import User
from django.test import TestCase

from apps.desafios.models import MissaoDiaria
from apps.desafios.services import data_atual_missoes, missoes_do_dia, registrar_exercicio_concluido
from apps.usuarios.models import Perfil
from apps.exercicios.models import Modulo, Secao, Estacao, Exercicio
from apps.mecanicas_jogo.services import marcar_exercicio_concluido


class MissoesDiariasTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='aventureiro', password='teste123')
        self.perfil = Perfil.objects.create(user=self.usuario)

    def test_cria_tres_missoes_sem_duplicar(self):
        self.assertEqual(len(missoes_do_dia(self.usuario)), 3)
        self.assertEqual(len(missoes_do_dia(self.usuario)), 3)
        self.assertEqual(MissaoDiaria.objects.filter(usuario=self.usuario, data=data_atual_missoes()).count(), 3)

    def test_progresso_e_recompensa_sao_limitados(self):
        registrar_exercicio_concluido(self.usuario, 10)
        registrar_exercicio_concluido(self.usuario, 10)
        registrar_exercicio_concluido(self.usuario, 10, estacao_concluida=True)
        missoes = {m.tipo: m for m in missoes_do_dia(self.usuario)}
        self.assertEqual([missoes[t].progresso for t in (MissaoDiaria.EXERCICIOS, MissaoDiaria.XP, MissaoDiaria.ESTACAO)], [3, 20, 1])
        self.assertTrue(all(m.concluida_em for m in missoes.values()))
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.cristal, 15)

        registrar_exercicio_concluido(self.usuario, 10, estacao_concluida=True)
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.cristal, 15)

    def test_conclusao_real_de_exercicio_atualiza_missoes(self):
        modulo = Modulo.objects.create(nome='C básico', descricao='Teste')
        secao = Secao.objects.create(modulo=modulo, nome='Introdução')
        estacao = Estacao.objects.create(secao=secao, nome='Primeira estação')
        exercicio = Exercicio.objects.create(
            modulo=modulo, estacao=estacao, tipo='info', titulo='Primeira lição', xp=10
        )
        marcar_exercicio_concluido(exercicio, self.perfil, self.usuario)
        missoes = {m.tipo: m for m in missoes_do_dia(self.usuario)}
        self.assertEqual(missoes[MissaoDiaria.EXERCICIOS].progresso, 1)
        self.assertEqual(missoes[MissaoDiaria.XP].progresso, 10)
        self.assertEqual(missoes[MissaoDiaria.ESTACAO].progresso, 1)
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.cristal, 5)

    def test_telas_exibem_missoes_do_dia(self):
        self.client.force_login(self.usuario)
        for caminho in ('/desafios/', '/exercicios/modulos/'):
            resposta = self.client.get(caminho)
            self.assertEqual(resposta.status_code, 200)
            self.assertContains(resposta, 'Conclua 3 exercícios')
            self.assertContains(resposta, 'Ganhe 20 XP')
            self.assertContains(resposta, 'Conclua 1 estação')
