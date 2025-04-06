from django.shortcuts import render, redirect

def landing_page(request):
    return render(request, 'landing.html')

def acesso_sem_login(request):
    
    return render(request, 'acesso_sem_login.html')
    