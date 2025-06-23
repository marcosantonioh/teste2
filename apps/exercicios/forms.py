from django import forms
from .models import Exercicio
from django import forms
from .models import Exercicio

# Campos base compartilhados por todos os formulários de exercício
BASE_EXERCICIO_FIELDS = [
    'titulo',
    'enunciado',
    'estacao',
    'modulo',
    'explicacao',
    'xp',
    # 'status' geralmente é gerenciado pelo sistema
]

# Widgets comuns
COMMON_WIDGETS = {
    'enunciado': forms.Textarea(attrs={'rows': 4, 'cols': 60}),
    'explicacao': forms.Textarea(attrs={'rows': 4, 'cols': 60}),
}

class ExercicioMultiplaEscolhaForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = BASE_EXERCICIO_FIELDS + [
            'tipo',
            'alternativa_1',
            'alternativa_2',
            'alternativa_3',
            'alternativa_4',
            'resposta_correta',
        ]
        widgets = {
            **COMMON_WIDGETS,
            'tipo': forms.HiddenInput(),
            'resposta_correta': forms.RadioSelect(choices=Exercicio.RESPOSTAS_CHOICES),
            'alternativa_1': forms.TextInput(attrs={'size': '60'}),
            'alternativa_2': forms.TextInput(attrs={'size': '60'}),
            'alternativa_3': forms.TextInput(attrs={'size': '60'}),
            'alternativa_4': forms.TextInput(attrs={'size': '60'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk: # Novo exercício
            self.fields['tipo'].initial = 'mcq'
        # Garante que o campo tipo não seja editável se já existir uma instância
        elif self.instance.pk and self.instance.tipo == 'mcq':
            self.fields['tipo'].disabled = True
        
        # Tornar campos de alternativa e resposta_correta obrigatórios
        self.fields['alternativa_1'].required = True
        self.fields['alternativa_2'].required = True
        # alternativa_3 e alternativa_4 podem ser opcionais dependendo da sua lógica
        # self.fields['alternativa_3'].required = False 
        # self.fields['alternativa_4'].required = False
        self.fields['resposta_correta'].required = True


class ExercicioCodigoLacunaForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = BASE_EXERCICIO_FIELDS + [
            'tipo',
            'codigo',
            'resposta_texto_codigo',
        ]
        widgets = {
            **COMMON_WIDGETS,
            'enunciado': forms.Textarea(attrs={'rows': 3, 'cols': 60, 'placeholder': 'Instruções para o aluno sobre o que fazer com o código abaixo.'}),
            'tipo': forms.HiddenInput(),
            'codigo': forms.Textarea(attrs={'rows': 10, 'cols': 60, 'placeholder': 'Ex: def minha_funcao(param):\n    # Preencha a lacuna para retornar o dobro de param\n    resultado = param * __LACUNA__\n    return resultado'}),
            'resposta_texto_codigo': forms.TextInput(attrs={'size': '60', 'placeholder': 'Texto exato que preenche a lacuna. Ex: 2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk: # Novo exercício
            self.fields['tipo'].initial = 'code'
        elif self.instance.pk and self.instance.tipo == 'code':
            self.fields['tipo'].disabled = True
        
        self.fields['codigo'].required = True
        self.fields['resposta_texto_codigo'].required = True


class ExercicioCombinacaoForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = BASE_EXERCICIO_FIELDS + [
            'tipo',
            'comb_par1_col1', 'comb_par1_col2',
            'comb_par2_col1', 'comb_par2_col2',
            'comb_par3_col1', 'comb_par3_col2',
            # Adicione mais campos de pares aqui se você os adicionou ao modelo
        ]
        widgets = {
            **COMMON_WIDGETS,
            'enunciado': forms.Textarea(attrs={'rows': 3, 'cols': 60, 'placeholder': 'Instrua o aluno a combinar os itens da Coluna 1 com os da Coluna 2.'}),
            'tipo': forms.HiddenInput(),
            'comb_par1_col1': forms.TextInput(attrs={'size': '40', 'placeholder': 'Item A1'}),
            'comb_par1_col2': forms.TextInput(attrs={'size': '40', 'placeholder': 'Item B1 (par de A1)'}),
            'comb_par2_col1': forms.TextInput(attrs={'size': '40', 'placeholder': 'Item A2'}),
            'comb_par2_col2': forms.TextInput(attrs={'size': '40', 'placeholder': 'Item B2 (par de A2)'}),
            'comb_par3_col1': forms.TextInput(attrs={'size': '40', 'placeholder': 'Item A3'}),
            'comb_par3_col2': forms.TextInput(attrs={'size': '40', 'placeholder': 'Item B3 (par de A3)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk: # Novo exercício
            self.fields['tipo'].initial = 'combinacao'
        elif self.instance.pk and self.instance.tipo == 'combinacao':
            self.fields['tipo'].disabled = True

        # Tornar pelo menos o primeiro par obrigatório
        self.fields['comb_par1_col1'].required = True
        self.fields['comb_par1_col2'].required = True
        # Você pode adicionar validações mais complexas se necessário (ex: se col1 preenchido, col2 também deve ser)

    def clean(self):
        cleaned_data = super().clean()
        # Exemplo de validação: se um item de um par é fornecido, o outro também deve ser.
        for i in range(1, 4): # Para 3 pares
            col1_field_name = f'comb_par{i}_col1'
            col2_field_name = f'comb_par{i}_col2'
            
            item_col1 = cleaned_data.get(col1_field_name)
            item_col2 = cleaned_data.get(col2_field_name)

            if item_col1 and not item_col2:
                self.add_error(col2_field_name, f"Se o item da Coluna 1 para o Par {i} é fornecido, o item correspondente da Coluna 2 também deve ser.")
            if item_col2 and not item_col1:
                self.add_error(col1_field_name, f"Se o item da Coluna 2 para o Par {i} é fornecido, o item correspondente da Coluna 1 também deve ser.")
        
        return cleaned_data


class ExercicioVerdadeiroFalsoForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = BASE_EXERCICIO_FIELDS + [
            'tipo',
            'resposta_vf_correta', # O enunciado já está em BASE_EXERCICIO_FIELDS
        ]
        widgets = {
            **COMMON_WIDGETS,
            'enunciado': forms.Textarea(attrs={'rows': 4, 'cols': 60, 'placeholder': 'Digite a afirmação que o aluno deverá julgar como Verdadeira ou Falsa.'}),
            'tipo': forms.HiddenInput(),
            'resposta_vf_correta': forms.RadioSelect(choices=[(True, 'Verdadeiro'), (False, 'Falso')]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk: # Novo exercício
            self.fields['tipo'].initial = 'vf'
        elif self.instance.pk and self.instance.tipo == 'vf':
            self.fields['tipo'].disabled = True
        
        # O campo 'enunciado' já é tratado pelo widget e sua obrigatoriedade
        # é definida no modelo (se blank=False).
        # Tornar a seleção de Verdadeiro/Falso obrigatória.
        # Para BooleanField com RadioSelect, null=False no modelo ou required=True no form garante isso.
        self.fields['resposta_vf_correta'].required = True
