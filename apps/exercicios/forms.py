from django import forms
from .models import Exercicio

class ExercicioForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = [
            'titulo',
            'enunciado',
            'alternativa_1',
            'alternativa_2',
            'alternativa_3',
            'alternativa_4',
            'resposta_correta',
            'dificuldade',
        ]
        widgets = {
            'enunciado': forms.Textarea(attrs={'rows': 6, 'cols': 60}),
            'resposta_correta': forms.RadioSelect(choices=Exercicio.RESPOSTAS_CHOICES),
        }
