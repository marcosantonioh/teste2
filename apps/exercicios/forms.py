from django import forms
from .models import Exercicio

class ExercicioForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = [
            'titulo',
            'enunciado',
            'estacao', 
            'modulo',  
            'tipo',    
            'codigo',   
            'alternativa_1',
            'alternativa_2',
            'alternativa_3',
            'alternativa_4',
            'resposta_correta',
            'explicacao', 
            'dificuldade',
            'xp',       
            'categoria',
            'origem',   
            # 'status' geralmente é gerenciado pelo sistema, mas pode ser incluído se necessário
        ]
        widgets = {
            'enunciado': forms.Textarea(attrs={'rows': 6, 'cols': 60}),
            'explicacao': forms.Textarea(attrs={'rows': 4, 'cols': 60}), # Widget para explicação
            'codigo': forms.Textarea(attrs={'rows': 10, 'cols': 60}), # Widget para código
            'resposta_correta': forms.RadioSelect(choices=Exercicio.RESPOSTAS_CHOICES),
            # Você pode adicionar mais widgets para outros campos se quiser customizar
            # a aparência deles (ex: 'tipo' como RadioSelect também).
        }

# Novo formulário para exercícios de preenchimento de lacuna em código
class ExercicioCodigoForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = [
            'titulo',
            'enunciado', # Pode ser uma breve instrução
            'estacao',
            'modulo',
            'tipo', # Será configurado como HiddenInput com valor 'code'
            'codigo', # Onde o professor insere o template do código com a(s) lacuna(s)
            'resposta_texto_codigo', # O novo campo para a resposta da lacuna
            'explicacao', # Explicação da resposta/lógica
            'dificuldade',
            'xp',
            'categoria',
            'origem',
        ]
        widgets = {
            'enunciado': forms.Textarea(attrs={'rows': 3, 'cols': 60, 'placeholder': 'Instruções para o aluno sobre o que fazer com o código abaixo.'}),
            'codigo': forms.Textarea(attrs={'rows': 10, 'cols': 60, 'placeholder': 'Ex: def minha_funcao(param):\n    # Preencha a lacuna para retornar o dobro de param\n    resultado = param * __LACUNA__\n    return resultado'}),
            'resposta_texto_codigo': forms.TextInput(attrs={'placeholder': 'Texto exato que preenche a lacuna. Ex: 2'}), # Ou Textarea se a resposta puder ser mais longa
            'explicacao': forms.Textarea(attrs={'rows': 4, 'cols': 60}),
            'tipo': forms.HiddenInput(), # Esconde o campo 'tipo' da interface do usuário
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define o valor inicial para o campo 'tipo' como 'code' e o torna oculto.
        # Isso garante que, ao criar um novo exercício com este formulário,
        # o tipo já venha preenchido como 'code'.
        if not self.instance.pk: # Apenas para formulários de criação (novas instâncias)
            self.fields['tipo'].initial = 'code'
        
        # Se você quiser que este formulário também edite apenas exercícios do tipo 'code',
        # você pode adicionar uma verificação aqui ou na view para garantir
        # que self.instance.tipo seja 'code' ao carregar dados para edição.