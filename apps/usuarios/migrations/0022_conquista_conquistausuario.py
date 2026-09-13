from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


CONQUISTAS_INICIAIS = [
    ("primeiros-passos", "Primeiros passos", "Conclua 5 exercícios.", 5),
    ("mente-analitica", "Mente analítica", "Conclua 15 exercícios.", 15),
    ("dominio-dos-loops", "Domínio dos loops", "Conclua 30 exercícios.", 30),
    ("construtor-avancado", "Construtor avançado", "Conclua 50 exercícios.", 50),
    ("guardiao-da-logica", "Guardião da lógica", "Conclua 75 exercícios.", 75),
    ("lenda-do-percurso", "Lenda do percurso", "Conclua 100 exercícios.", 100),
]


def criar_conquistas_iniciais(apps, schema_editor):
    Conquista = apps.get_model("usuarios", "Conquista")
    for codigo, nome, descricao, meta in CONQUISTAS_INICIAIS:
        Conquista.objects.update_or_create(
            codigo=codigo,
            defaults={
                "nome": nome,
                "descricao": descricao,
                "tipo_requisito": "exercicios_concluidos",
                "meta": meta,
            },
        )


def remover_conquistas_iniciais(apps, schema_editor):
    Conquista = apps.get_model("usuarios", "Conquista")
    Conquista.objects.filter(codigo__in=[item[0] for item in CONQUISTAS_INICIAIS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0021_perfil_avatar"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Conquista",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.SlugField(unique=True)),
                ("nome", models.CharField(max_length=100)),
                ("descricao", models.CharField(max_length=255)),
                ("tipo_requisito", models.CharField(choices=[("exercicios_concluidos", "Exercícios concluídos")], max_length=30)),
                ("meta", models.PositiveIntegerField()),
            ],
            options={"ordering": ["meta", "nome"]},
        ),
        migrations.CreateModel(
            name="ConquistaUsuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("conquistada_em", models.DateTimeField(auto_now_add=True)),
                ("conquista", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="usuarios", to="usuarios.conquista")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="conquistas", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-conquistada_em"], "unique_together": {("usuario", "conquista")}},
        ),
        migrations.RunPython(criar_conquistas_iniciais, remover_conquistas_iniciais),
    ]
