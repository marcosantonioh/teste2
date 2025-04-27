from django.contrib import admin
from .models import Exercicio, Modulo, Secao, Estacao

# Register your models here.
admin.site.register(Exercicio)
admin.site.register(Modulo)
admin.site.register(Secao)
admin.site.register(Estacao)