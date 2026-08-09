import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.exercicios.models import Estacao, Exercicio, Modulo, Secao


class Command(BaseCommand):
    help = "Carrega o conteúdo inicial de ensino sem duplicar a demonstração."

    def handle(self, *args, **options):
        fixture_path = (
            settings.BASE_DIR
            / "apps"
            / "exercicios"
            / "fixtures"
            / "conteudo_inicial.json"
        )

        if not fixture_path.exists():
            raise CommandError(f"Fixture não encontrada: {fixture_path}")

        with fixture_path.open(encoding="utf-8") as fixture_file:
            registros = json.load(fixture_file)

        modulos = {}
        secoes = {}
        estacoes = {}

        # A demonstração já é criada pela migração 0026. Não a duplicamos.
        for registro in registros:
            if registro["model"] != "exercicios.modulo":
                continue

            campos = registro["fields"]
            if campos["nome"] == "Demonstração":
                continue

            modulo, criado = Modulo.objects.get_or_create(
                nome=campos["nome"],
                defaults={
                    "descricao": campos["descricao"],
                    "ordem": campos["ordem"],
                },
            )
            modulos[registro["pk"]] = modulo
            if criado:
                self.stdout.write(f"Módulo criado: {modulo.nome}")

        for registro in registros:
            if registro["model"] != "exercicios.secao":
                continue

            campos = registro["fields"]
            modulo = modulos.get(campos["modulo"])
            if not modulo:
                continue

            secao, _ = Secao.objects.get_or_create(
                modulo=modulo,
                nome=campos["nome"],
                defaults={"status": campos["status"], "ordem": campos["ordem"]},
            )
            secoes[registro["pk"]] = secao

        for registro in registros:
            if registro["model"] != "exercicios.estacao":
                continue

            campos = registro["fields"]
            secao = secoes.get(campos["secao"])
            if not secao:
                continue

            estacao, _ = Estacao.objects.get_or_create(
                secao=secao,
                nome=campos["nome"],
                defaults={
                    "status": campos["status"],
                    "disponivel_para_visitantes": campos[
                        "disponivel_para_visitantes"
                    ],
                },
            )
            estacoes[registro["pk"]] = estacao

        exercicios_criados = 0
        for registro in registros:
            if registro["model"] != "exercicios.exercicio":
                continue

            campos = registro["fields"].copy()
            modulo = modulos.get(campos.pop("modulo"))
            estacao = estacoes.get(campos.pop("estacao"))
            if not modulo or not estacao:
                continue

            titulo = campos.pop("titulo")
            _, criado = Exercicio.objects.get_or_create(
                estacao=estacao,
                titulo=titulo,
                defaults={"modulo": modulo, **campos},
            )
            exercicios_criados += int(criado)

        self.stdout.write(
            self.style.SUCCESS(
                f"Conteúdo inicial verificado. Exercícios novos: {exercicios_criados}."
            )
        )
