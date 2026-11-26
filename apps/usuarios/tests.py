import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.contrib.auth.models import User
from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from apps.exercicios.models import Estacao, Exercicio, ExercicioUsuario, Modulo, Secao

from .models import Amizade, ConquistaUsuario, Perfil
from .services import restaurar_vidas_usuario, sincronizar_conquistas


class RestauracaoVidasTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="aluno-vidas")
        self.perfil = Perfil.objects.create(user=self.user)

    def test_restaura_uma_vida_por_intervalo_preservando_tempo_parcial(self):
        agora = timezone.now()
        self.perfil.vidas_atuais = 1
        self.perfil.ultima_restauracao_vida = agora - datetime.timedelta(minutes=35)
        self.perfil.save(update_fields=["vidas_atuais", "ultima_restauracao_vida"])

        restaurar_vidas_usuario(self.user, agora=agora)
        self.perfil.refresh_from_db()

        self.assertEqual(self.perfil.vidas_atuais, 3)
        self.assertEqual(
            self.perfil.ultima_restauracao_vida,
            agora - datetime.timedelta(minutes=5),
        )
        restaurar_vidas_usuario(self.user, agora=agora)
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.vidas_atuais, 3)

    def test_periodo_offline_longo_para_no_limite(self):
        agora = timezone.now()
        self.perfil.vidas_atuais = 0
        self.perfil.ultima_restauracao_vida = agora - datetime.timedelta(days=1)
        self.perfil.save(update_fields=["vidas_atuais", "ultima_restauracao_vida"])

        restaurar_vidas_usuario(self.user, agora=agora)
        self.perfil.refresh_from_db()

        self.assertEqual(self.perfil.vidas_atuais, self.perfil.max_vidas)
        self.assertEqual(self.perfil.ultima_restauracao_vida, agora)

    def test_endpoint_restaura_vidas_e_informa_proximo_prazo(self):
        self.perfil.vidas_atuais = 0
        self.perfil.ultima_restauracao_vida = timezone.now() - datetime.timedelta(minutes=16)
        self.perfil.save(update_fields=["vidas_atuais", "ultima_restauracao_vida"])
        self.client.force_login(self.user)

        response = self.client.get(reverse("exercicios:estado_vidas"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["vidas_atuais"], 1)
        self.assertGreater(response.json()["segundos_proxima_vida"], 0)

    def test_resposta_pode_ser_enviada_apos_vida_voltar(self):
        modulo = Modulo.objects.create(nome="Loops", descricao="Teste")
        secao = Secao.objects.create(nome="Introdução", modulo=modulo)
        estacao = Estacao.objects.create(nome="Estação", secao=secao)
        exercicio = Exercicio.objects.create(
            modulo=modulo, estacao=estacao, tipo="mcq", resposta_correta="1", xp=10,
        )
        self.perfil.vidas_atuais = 0
        self.perfil.ultima_restauracao_vida = timezone.now() - datetime.timedelta(minutes=16)
        self.perfil.save(update_fields=["vidas_atuais", "ultima_restauracao_vida"])
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("exercicios:resolver_exercicio", args=[exercicio.id]),
            {"acao": "responder", "is_ajax_request": "1", "resposta": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.vidas_atuais, 1)
        self.assertEqual(self.perfil.xp, 10)

    def test_perda_da_primeira_vida_inicia_novo_prazo(self):
        from apps.mecanicas_jogo.services import processar_resposta_exercicio

        modulo = Modulo.objects.create(nome="Loops", descricao="Teste")
        secao = Secao.objects.create(nome="Introdução", modulo=modulo)
        estacao = Estacao.objects.create(nome="Estação", secao=secao)
        exercicio = Exercicio.objects.create(
            modulo=modulo, estacao=estacao, tipo="mcq", resposta_correta="2",
        )
        self.perfil.ultima_restauracao_vida = timezone.now() - datetime.timedelta(days=1)
        self.perfil.save(update_fields=["ultima_restauracao_vida"])
        antes = timezone.now()

        processar_resposta_exercicio("1", exercicio, self.perfil, self.user)
        self.perfil.refresh_from_db()

        self.assertEqual(self.perfil.vidas_atuais, self.perfil.max_vidas - 1)
        self.assertGreaterEqual(self.perfil.ultima_restauracao_vida, antes)
        self.assertLessEqual(self.perfil.ultima_restauracao_vida, timezone.now())


@skipUnless(connection.vendor == "postgresql", "Bloqueio de linha exige PostgreSQL")
class RestauracaoVidasConcorrenteTests(TransactionTestCase):
    def test_duas_consultas_simultaneas_restauram_uma_vida(self):
        usuario = User.objects.create_user(username="aluno-vidas-concorrente")
        perfil = Perfil.objects.create(user=usuario, vidas_atuais=0)
        agora = timezone.now()
        perfil.ultima_restauracao_vida = agora - datetime.timedelta(minutes=16)
        perfil.save(update_fields=["ultima_restauracao_vida"])
        largada = Barrier(2)

        def consultar():
            close_old_connections()
            try:
                largada.wait(timeout=10)
                restaurar_vidas_usuario(usuario, agora=agora)
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = [executor.submit(consultar) for _ in range(2)]
            for resultado in resultados:
                resultado.result(timeout=20)

        perfil.refresh_from_db()
        self.assertEqual(perfil.vidas_atuais, 1)


class AvatarPerfilTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="estudante", email="estudante@example.com", password="senha-segura"
        )
        self.perfil = Perfil.objects.create(user=self.user)
        self.client.force_login(self.user)

    def test_avatar_padrao_tem_arquivo_estatico(self):
        self.assertEqual(self.perfil.avatar, "coruja-logica")
        self.assertEqual(self.perfil.avatar_arquivo, "img/avatares/comuns/Coruja Lógica.png")

    def test_usuario_pode_selecionar_avatar_do_catalogo(self):
        response = self.client.post(
            reverse("usuarios:editar_perfil"),
            {
                "action": "salvar_perfil",
                "Nome": self.user.username,
                "email": self.user.email,
                "bio": "Aprendendo loops.",
                "avatar": "robo-aprendiz",
            },
        )

        self.assertRedirects(response, reverse("usuarios:editar_perfil"))
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.avatar, "robo-aprendiz")
        self.assertEqual(self.perfil.bio, "Aprendendo loops.")

    def test_avatar_invalido_nao_substitui_a_escolha_atual(self):
        self.perfil.avatar = "panda-code"
        self.perfil.save()

        self.client.post(
            reverse("usuarios:editar_perfil"),
            {
                "action": "salvar_perfil",
                "Nome": self.user.username,
                "email": self.user.email,
                "bio": "",
                "avatar": "arquivo-enviado-pelo-usuario",
            },
        )

        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.avatar, "panda-code")

    def test_conquista_desbloqueia_avatar_raro(self):
        modulo = Modulo.objects.create(nome="Lógica", descricao="Base")
        secao = Secao.objects.create(modulo=modulo, nome="Início")
        estacao = Estacao.objects.create(secao=secao, nome="Estação inicial")
        for indice in range(5):
            exercicio = Exercicio.objects.create(
                modulo=modulo,
                estacao=estacao,
                titulo=f"Exercício {indice}",
                tipo="info",
            )
            ExercicioUsuario.objects.create(
                usuario=self.user, exercicio=exercicio, status="concluido"
            )

        sincronizar_conquistas(self.user)

        self.assertTrue(
            ConquistaUsuario.objects.filter(
                usuario=self.user, conquista__codigo="primeiros-passos"
            ).exists()
        )
        self.assertTrue(self.perfil.avatar_desbloqueado("explorador-cyber"))


class AmizadeTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user(username='ana', password='senha-segura')
        self.bruno = User.objects.create_user(username='bruno', password='senha-segura')
        self.carla = User.objects.create_user(username='carla', password='senha-segura')
        for usuario in (self.ana, self.bruno, self.carla):
            Perfil.objects.create(user=usuario)

    def test_enviar_e_aceitar_solicitacao(self):
        self.client.force_login(self.ana)
        resposta = self.client.post(reverse('usuarios:enviar_solicitacao', args=[self.bruno.id]))
        self.assertEqual(resposta.status_code, 302)
        amizade = Amizade.objects.get(remetente=self.ana, destinatario=self.bruno)
        self.assertEqual(amizade.status, Amizade.STATUS_PENDENTE)

        self.client.force_login(self.bruno)
        resposta = self.client.post(reverse('usuarios:aceitar_solicitacao', args=[amizade.id]))
        self.assertEqual(resposta.status_code, 302)
        amizade.refresh_from_db()
        self.assertEqual(amizade.status, Amizade.STATUS_ACEITA)

    def test_apenas_destinatario_responde_solicitacao(self):
        amizade = Amizade.objects.create(remetente=self.ana, destinatario=self.bruno)
        self.client.force_login(self.carla)
        resposta = self.client.post(reverse('usuarios:aceitar_solicitacao', args=[amizade.id]))
        self.assertEqual(resposta.status_code, 404)
        amizade.refresh_from_db()
        self.assertEqual(amizade.status, Amizade.STATUS_PENDENTE)

    def test_menu_exibe_notificacao_para_solicitacao_recebida(self):
        Amizade.objects.create(remetente=self.ana, destinatario=self.bruno)
        self.client.force_login(self.bruno)

        resposta = self.client.get(reverse('usuarios:amigos'))

        self.assertContains(resposta, 'notificacao-amigos')
        self.assertContains(resposta, '1 solicitações de amizade pendentes')

    def test_nao_cria_solicitacao_para_si_mesmo_ou_duplicada(self):
        self.client.force_login(self.ana)
        self.client.post(reverse('usuarios:enviar_solicitacao', args=[self.ana.id]))
        self.assertFalse(Amizade.objects.exists())

        Amizade.objects.create(remetente=self.bruno, destinatario=self.ana)
        self.client.post(reverse('usuarios:enviar_solicitacao', args=[self.bruno.id]))
        self.assertEqual(Amizade.objects.count(), 1)


class EdicaoPerfilAbasTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='perfil-abas', password='SenhaAntiga123!')
        self.perfil = Perfil.objects.create(user=self.usuario)
        self.client.force_login(self.usuario)
        self.url = reverse('usuarios:editar_perfil')

    def test_todas_as_abas_abrem_com_conteudo(self):
        titulos = {
            'informacoes': 'Informações',
            'preferencias': 'Preferências',
            'senha': 'Mudar senha',
            'links': 'Seus links',
            'conexoes': 'Conexões',
            'notificacoes': 'Notificações',
        }
        for aba, titulo in titulos.items():
            with self.subTest(aba=aba):
                resposta = self.client.get(self.url, {'secao': aba})
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(resposta.context['aba_ativa'], aba)
                self.assertContains(resposta, titulo)

    def test_preferencias_salvam_e_rejeitam_valores_invalidos(self):
        resposta = self.client.post(self.url, {
            'action': 'salvar_preferencias', 'tema': 'escuro', 'visibilidade': 'privado',
        })
        self.assertRedirects(resposta, self.url + '?secao=preferencias')
        self.perfil.refresh_from_db()
        self.assertEqual((self.perfil.tema, self.perfil.visibilidade), ('escuro', 'privado'))
        self.client.post(self.url, {
            'action': 'salvar_preferencias', 'tema': 'invalido', 'visibilidade': 'publico',
        })
        self.perfil.refresh_from_db()
        self.assertEqual((self.perfil.tema, self.perfil.visibilidade), ('escuro', 'privado'))

    def test_troca_de_senha_preserva_sessao(self):
        resposta = self.client.post(self.url, {
            'action': 'alterar_senha', 'old_password': 'SenhaAntiga123!',
            'new_password1': 'SenhaNova456!', 'new_password2': 'SenhaNova456!',
        })
        self.assertRedirects(resposta, self.url + '?secao=senha')
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('SenhaNova456!'))
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_formulario_de_senha_em_portugues(self):
        resposta = self.client.get(self.url, {'secao': 'senha'})
        self.assertContains(resposta, 'Senha antiga')
        self.assertContains(resposta, 'Nova senha')
        self.assertContains(resposta, 'Confirmação da nova senha')
        self.assertNotContains(resposta, 'Old password')

    def test_links_https_salvos_e_exibidos_no_perfil(self):
        resposta = self.client.post(self.url, {
            'action': 'salvar_links', 'link_site': 'http://exemplo.com',
            'link_github': '', 'link_linkedin': '',
        })
        self.assertEqual(resposta.status_code, 200)
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.link_site, '')
        resposta = self.client.post(self.url, {
            'action': 'salvar_links', 'link_site': 'https://exemplo.com',
            'link_github': '', 'link_linkedin': '',
        })
        self.assertRedirects(resposta, self.url + '?secao=links')
        self.assertContains(self.client.get(reverse('usuarios:perfil_usuario')), 'https://exemplo.com')

    def test_notificacoes_permite_aceitar_solicitacao(self):
        outro = User.objects.create_user(username='outro-aluno')
        Perfil.objects.create(user=outro)
        amizade = Amizade.objects.create(remetente=outro, destinatario=self.usuario)
        self.assertContains(self.client.get(self.url, {'secao': 'notificacoes'}), 'outro-aluno')
        resposta = self.client.post(
            reverse('usuarios:aceitar_solicitacao', args=[amizade.pk]),
            {'next': self.url + '?secao=notificacoes'},
        )
        self.assertRedirects(resposta, self.url + '?secao=notificacoes')
        amizade.refresh_from_db()
        self.assertEqual(amizade.status, Amizade.STATUS_ACEITA)
        self.assertContains(self.client.get(self.url, {'secao': 'conexoes'}), 'outro-aluno')
