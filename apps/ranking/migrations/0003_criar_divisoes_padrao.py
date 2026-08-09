from django.db import migrations


DIVISOES_PADRAO = [
    ("Bronze", "img/ranking/bronze.svg"),
    ("Prata", "img/ranking/prata.svg"),
    ("Ouro", "img/ranking/ouro.svg"),
    ("Esmeralda", "img/ranking/esmeralda.svg"),
    ("Rubi", "img/ranking/rubi.svg"),
    ("Ametista", "img/ranking/ametista.svg"),
    ("Diamante", "img/ranking/diamante.svg"),
]


def criar_divisoes_padrao(apps, schema_editor):
    Divisao = apps.get_model("ranking", "Divisao")
    for nome, imagem in DIVISOES_PADRAO:
        Divisao.objects.get_or_create(nome=nome, defaults={"imagem": imagem})


class Migration(migrations.Migration):

    dependencies = [
        ("ranking", "0002_alter_divisao_imagem_alter_divisao_nome"),
    ]

    operations = [
        migrations.RunPython(criar_divisoes_padrao, migrations.RunPython.noop),
    ]
