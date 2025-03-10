from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required(login_url="login_usuario")
def main_view(request):
    return render( request, 'exercicios/main.html')


def lista_exercicios(request):
    return render(request, 'exercicios/lista_exercicios.html')



def ranking():
    
    return 