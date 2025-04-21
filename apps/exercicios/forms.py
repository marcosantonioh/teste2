from django import forms
from .models import Exercicio

class SubmissaoForm(forms.Form):
    resposta = forms.CharField(widget=forms.Textarea, label="Sua Resposta")

