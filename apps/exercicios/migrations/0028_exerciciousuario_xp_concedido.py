from django.db import migrations, models


def preservar_xp_de_progresso_existente(apps, schema_editor):
    """Considera como já concedido o XP de exercícios já concluídos."""
    ExercicioUsuario = apps.get_model("exercicios", "ExercicioUsuario")
    ExercicioUsuario.objects.filter(status="concluido").update(xp_concedido=True)


class Migration(migrations.Migration):

    dependencies = [
        ("exercicios", "0027_remove_exercicio_status_exerciciousuario"),
    ]

    operations = [
        migrations.AddField(
            model_name="exerciciousuario",
            name="xp_concedido",
            field=models.BooleanField(
                default=False,
                help_text="Indica se o XP deste exercício já foi entregue ao usuário.",
            ),
        ),
        migrations.RunPython(
            preservar_xp_de_progresso_existente,
            migrations.RunPython.noop,
        ),
    ]
