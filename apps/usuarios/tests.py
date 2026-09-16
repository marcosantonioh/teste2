from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.exercicios.models import Estacao, Exercicio, ExercicioUsuario, Modulo, Secao

from .models import Amizade, ConquistaUsuario, Perfil
from .services import sincronizar_conquistas


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
