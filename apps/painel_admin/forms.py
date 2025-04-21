from django import forms
from apps.exercicios.models import Exercicio

class ExercicioForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = [
            'titulo', 'descricao', 'tipo', 'categoria', 'dificuldade', 'xp',
            'bloqueado', 'concluido', 'modulo'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'bloqueado': forms.CheckboxInput(),
            'concluido': forms.CheckboxInput(),
        }
