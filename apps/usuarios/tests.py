from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Perfil


class AvatarPerfilTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="estudante", email="estudante@example.com", password="senha-segura"
        )
        self.perfil = Perfil.objects.create(user=self.user)
        self.client.force_login(self.user)

    def test_avatar_padrao_tem_arquivo_estatico(self):
        self.assertEqual(self.perfil.avatar, "coruja-logica")
        self.assertEqual(self.perfil.avatar_arquivo, "img/avatares/Coruja Lógica.png")

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
