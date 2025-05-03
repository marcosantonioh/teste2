from django import forms
from .models import Exercicio

class ExercicioForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = [
            'titulo',
            'descricao',
            'alternativa_a',
            'alternativa_b',
            'alternativa_c',
            'alternativa_d',
            'resposta_correta',
            'dificuldade',
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 6, 'cols': 60}),
            'resposta_correta': forms.RadioSelect(choices=Exercicio.RESPOSTAS_CHOICES),
        }
