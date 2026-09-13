from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.exercicios.models import Estacao, Exercicio, ExercicioUsuario, Modulo, Secao

from .models import ConquistaUsuario, Perfil
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
