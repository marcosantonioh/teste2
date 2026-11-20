from django.db import migrations


def definir_ilustracao_matriz(apps, schema_editor):
    Modulo = apps.get_model("exercicios", "Modulo")
    Modulo.objects.filter(nome__iexact="Matriz", imagem="").update(
        imagem="img/modulos/matrizes.svg"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("exercicios", "0036_sequencia_iniciante_visitante"),
    ]

    operations = [
        migrations.RunPython(definir_ilustracao_matriz, migrations.RunPython.noop),
    ]
