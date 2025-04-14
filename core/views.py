from django.shortcuts import render, redirect

def landing_page(request):
    return render(request, 'landing.html')


    
    
def etapa(request, numero):
    
    etapas = {
        1: {
            "titulo": "Bem-vindo ao GameLoops!",
            "mensagem": "Vamos começar sua jornada no mundo da lógica de programação em C.",
            "tipo": "texto",
        },
        2: {
            "titulo": "Você está no lugar certo!",
            "mensagem": "GameLoops foi feito para quem quer aprender de forma fácil e divertida.",
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
                ("Leve", "5 minutos"),
                ("Regular", "10 minutos"),
                ("Foco total", "20 minutos"),
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

    # Se for POST, salva a resposta e vai pra próxima
    if request.method == "POST":
        resposta = request.POST.get('nivel')
        request.session[f'resposta_etapa_{numero}'] = resposta
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
        'proxima_etapa': numero + 1
    }
    return render(request, 'onboarding.html', contexto)
