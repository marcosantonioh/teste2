from django.db import migrations


def preparar_demonstracao(apps, schema_editor):
    Modulo = apps.get_model('exercicios', 'Modulo')
    Secao = apps.get_model('exercicios', 'Secao')
    Estacao = apps.get_model('exercicios', 'Estacao')
    Exercicio = apps.get_model('exercicios', 'Exercicio')

    modulo, _ = Modulo.objects.get_or_create(
        nome='Demonstração',
        defaults={'descricao': 'Primeiros passos em programação com C.', 'ordem': 0},
    )
    secao, _ = Secao.objects.get_or_create(
        modulo=modulo, nome='Experimente a Cventure', defaults={'ordem': 0},
    )
    estacao, _ = Estacao.objects.get_or_create(
        secao=secao, nome='Primeiros passos em C',
        defaults={'disponivel_para_visitantes': True},
    )
    Estacao.objects.filter(pk=estacao.pk).update(disponivel_para_visitantes=True)

    # A demonstração usa a ordem de criação (id). Mantemos os três itens
    # existentes e acrescentamos uma progressão que termina com uma conquista.
    novos = [
        {
            'titulo': 'Primeira mensagem em C',
            'enunciado': 'Em C, printf mostra uma mensagem na tela. O que este código exibe?',
            'codigo': 'printf("Olá, mundo!");',
            'tipo': 'mcq',
            'alternativa_1': 'Olá, mundo!',
            'alternativa_2': 'printf',
            'alternativa_3': 'Nada',
            'alternativa_4': 'Uma conta',
            'resposta_correta': '1',
            'explicacao': 'O texto entre aspas é exibido pelo printf.',
        },
        {
            'titulo': 'Mudando o valor de uma variável',
            'enunciado': 'Uma variável pode guardar um valor que muda. Qual número será mostrado?',
            'codigo': 'int pontos = 2;\npontos = 4;\nprintf("%d", pontos);',
            'tipo': 'mcq',
            'alternativa_1': '2',
            'alternativa_2': '4',
            'alternativa_3': '6',
            'alternativa_4': '24',
            'resposta_correta': '2',
            'explicacao': 'A segunda atribuição substitui o valor anterior de pontos.',
        },
        {
            'titulo': 'Complete a soma',
            'enunciado': 'Digite somente o número que falta para o resultado ser 5.',
            'codigo': 'int resultado = 2 + ___;\nprintf("%d", resultado);',
            'tipo': 'lacuna',
            'resposta_texto_codigo': '3',
            'explicacao': 'Dois mais três é igual a cinco.',
        },
        {
            'titulo': 'Uma primeira decisão',
            'enunciado': 'Se a condição é verdadeira, o programa executa o bloco dentro de if. O que aparece na tela?',
            'codigo': 'int idade = 18;\nif (idade >= 18) {\n    printf("Pode entrar");\n}',
            'tipo': 'mcq',
            'alternativa_1': 'Pode entrar',
            'alternativa_2': 'Não pode entrar',
            'alternativa_3': '18',
            'alternativa_4': 'Nada',
            'resposta_correta': '1',
            'explicacao': '18 é maior ou igual a 18; por isso o bloco é executado.',
        },
    ]
    for dados in novos:
        titulo = dados.pop('titulo')
        Exercicio.objects.get_or_create(
            estacao=estacao, titulo=titulo,
            defaults={'modulo': modulo, 'xp': 0, **dados},
        )


class Migration(migrations.Migration):
    dependencies = [('exercicios', '0035_modulo_imagem')]

    operations = [migrations.RunPython(preparar_demonstracao, migrations.RunPython.noop)]
