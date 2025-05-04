from django.contrib.auth.decorators import login_required
from apps.usuarios.models import Perfil
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from apps.exercicios.models import Exercicio, Modulo, Secao, Estacao
from django.http import Http404



# @login_required(login_url="usuarios:login_usuario")
def main_view(request):
    perfil = None
    if request.user.is_authenticated:
        try:
            perfil = Perfil.objects.get(user=request.user)
        except ObjectDoesNotExist:
            perfil = Perfil.objects.create(user=request.user)

    # Caso o usuário não esteja logado e não tenha feito o onboarding, redireciona
    elif not request.session.get('onboarding_concluido'):
        return redirect('etapa', 1)  # ou qual for o nome da sua view inicial

    
    context = {
        'perfil': perfil
    }
    return render( request, 'exercicios/main.html', context)


# @login_required(login_url="usuarios:login_usuario")
def modulos(request):
    perfil = None

    if request.user.is_authenticated:
        try:
            perfil = Perfil.objects.get(user=request.user)
        except ObjectDoesNotExist:
            perfil = Perfil.objects.create(user=request.user)

    modulos = Modulo.objects.all()

    context = {
        'perfil': perfil,  # Vai ser None se o usuário for anônimo
        'modulos': modulos
    }
    return render(request, 'exercicios/modulos.html', context)




def percurso(request, modulo_id):
    
    # Obtém o módulo com o id fornecido
    modulo = get_object_or_404(Modulo, pk=modulo_id)
    secoes = Secao.objects.filter(modulo=modulo)

    # Para cada seção, você pode obter as estações
    for secao in secoes:
        secao.estacoes_list = Estacao.objects.filter(secao=secao)
        for estacao in secao.estacoes_list:
            estacao.exercicios_list = Exercicio.objects.filter(estacao=estacao)

    context = {
        'modulo': modulo,
        'secoes': secoes  # Passa as seções para o template
    }
    
    # Adicione o módulo ao contexto e renderize o template
    return render(request, 'exercicios/percurso.html', context)





def lista_exercicios(request, modulo_id):
    try:
        perfil = Perfil.objects.get(user=request.user)
    except ObjectDoesNotExist:
        perfil = Perfil.objects.create(user=request.user)

    modulo = get_object_or_404(Modulo, pk=modulo_id)
    exercicios = Exercicio.objects.filter(modulo=modulo).order_by('bloqueado')

    context = {
        'perfil': perfil,
        'modulo': modulo,
        'exercicios': exercicios
    }
    
    return render(request, 'exercicios/lista_exercicios.html', context)





def resolver_exercicio(request, exercicio_id):
    exercicio = get_object_or_404(Exercicio, id=exercicio_id)
    resultado = None
    correta = None
    perfil = Perfil.objects.get(user=request.user)

    try:
        perfil = Perfil.objects.get(user=request.user)
    except Perfil.DoesNotExist:
        raise Http404("Perfil não encontrado")

    if request.method == 'POST':
        if exercicio.tipo == 'mcq':
            resposta_usuario = request.POST.get('resposta')
            correta = resposta_usuario == exercicio.resposta_correta
        elif exercicio.tipo == 'code':
            resposta_usuario = request.POST.get('codigo', '').strip()
            correta = resposta_usuario == exercicio.resposta_correta.strip()

        resultado = 'correto' if correta else 'incorreto'

        # Reduz uma vida se errar
        if not correta:
            if perfil.vidas > 0:
                perfil.vidas -= 1
                perfil.save()

    return render(request, 'exercicios/resolver_exercicio.html', {
        'exercicio': exercicio,
        'resultado': resultado,
        'correta': correta,
        'perfil': perfil,
        'modulo_id': exercicio.modulo.id,  # ou como for o relacionamento
    })

