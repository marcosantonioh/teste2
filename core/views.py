from django.shortcuts import render, redirect
from django.urls import reverse


TEMPOS_ESTUDO_VALIDOS = {'leve', 'regular', 'foco_total'}

def landing_page(request):
    if request.user.is_authenticated:
        print("⚠️ Usuário logado:", request.user.username)
    return render(request, 'landing.html')


    
    
def etapa(request, numero):
    
    etapas = {
        1: {
            "titulo": "Bem-vindo ao Cventure!",
            "mensagem": "Cventure foi feito para quem quer aprender de forma fácil e divertida.",
            "tipo": "texto",
        },
        2: {
            "titulo": "Você está no lugar certo!",
            "mensagem": "Vamos começar sua jornada no mundo da lógica de programação em C.",
            "tipo": "texto",
        },
        3: {
            "titulo": "Prepare-se!",
            "mensagem": "Vamos te mostrar como tudo funciona com exemplos práticos e gamificação.",
            "tipo": "texto",
        },
        4: {
            "titulo": "Quanto tempo você quer gastar aprendendo?",
            "tipo": "opcoes",
            "opcoes": [
                ("leve", "5 minutos"),
                ("regular", "10 minutos"),
                ("foco_total", "20 minutos"),
            ]
        },
        5: {
            "titulo": "Fique por dentro !",
            "mensagem": "Podemos te avisar quando novos desafios estiverem disponíveis, ou quando você estiver perto de conquistar um novo nível.",
            "tipo": "notification",
        },
        6: {
            "titulo": "Só um segundo... !",
            "mensagem": "Iniciando Ambiente.",
            "tipo": "carregamento",
        },
    }

    etapa_info = etapas.get(numero)
    if not etapa_info:
        return redirect('etapa', numero=1)  # Redireciona para a primeira se não existir

    # A única etapa com formulário registra a preferência de estudo do visitante.
    if request.method == "POST":
        if numero != 4:
            return redirect('etapa', numero=numero)

        tempo_estudo = request.POST.get('tempo')
        if tempo_estudo not in TEMPOS_ESTUDO_VALIDOS:
            return redirect('etapa', numero=4)

        request.session['tempo_estudo'] = tempo_estudo
        return redirect('etapa', numero + 1)

    # ✅ Marcar que concluiu o onboarding na última etapa
    if numero == 6:
        request.session['onboarding_concluido'] = True
        

    contexto = {
        'titulo': etapa_info.get("titulo"),
        'mensagem': etapa_info.get("mensagem"),
        'opcoes': etapa_info.get("opcoes"),
        'tipo': etapa_info.get("tipo", "texto"),
        'etapa_atual': numero,
        'proxima_etapa': numero + 1,
        'destino_final': reverse(
            'exercicios:modulos'
            if request.user.is_authenticated
            else 'exercicios:iniciar_demo'
        ),
    }
    return render(request, 'onboarding.html', contexto)
