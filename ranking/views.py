from django.shortcuts import render
from .models import Exercicio, Usuario

def lista_exercicios(request):
    exercicios = Exercicio.objects.all()  # Obtém todos os exercícios
    return render(request, 'exercicios/exercicios.html', {'exercicios': exercicios})

def ranking(request):
    usuarios = Usuario.objects.all().order_by('-pontuacao')[:10]  # Top 10 usuários com maior pontuação
    return render(request, 'ranking.html', {'usuarios': usuarios})
