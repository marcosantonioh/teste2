from django import forms
from .models import Exercicio
from django import forms
from .models import Exercicio

# Campos base compartilhados por todos os formulários de exercício
BASE_EXERCICIO_FIELDS = [
    "titulo",
    "enunciado",
    "estacao",
    "modulo",
    "explicacao",
    "xp",
    # 'status' geralmente é gerenciado pelo sistema
]

# Widgets comuns
COMMON_WIDGETS = {
    "enunciado": forms.Textarea(attrs={"rows": 4, "cols": 60}),
    "explicacao": forms.Textarea(attrs={"rows": 4, "cols": 60}),
}


class ExercicioMultiplaEscolhaForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = BASE_EXERCICIO_FIELDS + [
            "tipo",
            "alternativa_1",
            "alternativa_2",
            "alternativa_3",
            "alternativa_4",
            "resposta_correta",
        ]
        widgets = {
            **COMMON_WIDGETS,
            "tipo": forms.HiddenInput(),
            "resposta_correta": forms.RadioSelect(choices=Exercicio.RESPOSTAS_CHOICES),
            "alternativa_1": forms.TextInput(attrs={"size": "60"}),
            "alternativa_2": forms.TextInput(attrs={"size": "60"}),
            "alternativa_3": forms.TextInput(attrs={"size": "60"}),
            "alternativa_4": forms.TextInput(attrs={"size": "60"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Novo exercício
            self.fields["tipo"].initial = "mcq"
        # Garante que o campo tipo não seja editável se já existir uma instância
        elif self.instance.pk and self.instance.tipo == "mcq":
            self.fields["tipo"].disabled = True

        # Tornar campos de alternativa e resposta_correta obrigatórios
        self.fields["alternativa_1"].required = True
        self.fields["alternativa_2"].required = True
        # alternativa_3 e alternativa_4 podem ser opcionais dependendo da sua lógica
        # self.fields['alternativa_3'].required = False
        # self.fields['alternativa_4'].required = False
        self.fields["resposta_correta"].required = True


class ExercicioLacunaForm(forms.ModelForm):
    respostas_aceitas = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "cols": 60,
                "placeholder": "Uma alternativa por linha. Ex:\n++contador\ncontador += 1",
            }
        ),
        help_text="Opcional. Informe uma resposta aceita por linha; espaços e ; final são ignorados.",
    )

    class Meta:
        model = Exercicio
        fields = BASE_EXERCICIO_FIELDS + [
            "tipo",
            "codigo",  # Reutilizando 'codigo' para o texto com a lacuna
            "resposta_texto_codigo",
            "respostas_aceitas",
        ]
        widgets = {
            **COMMON_WIDGETS,
            "enunciado": forms.Textarea(
                attrs={
                    "rows": 3,
                    "cols": 60,
                    "placeholder": "Instrua o aluno a preencher a lacuna no texto ou código abaixo.",
                }
            ),
            "tipo": forms.HiddenInput(),
            "codigo": forms.Textarea(
                attrs={
                    "rows": 10,
                    "cols": 60,
                    "placeholder": "Ex: A capital do Brasil é __LACUNA__.",
                }
            ),
            "resposta_texto_codigo": forms.TextInput(
                attrs={
                    "size": "60",
                    "placeholder": "Texto exato que preenche a lacuna. Ex: Brasília",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["tipo"].initial = "lacuna"
        elif self.instance.pk and self.instance.tipo == "lacuna":
            self.fields["tipo"].disabled = True

        self.fields["codigo"].required = True
        self.fields["codigo"].help_text = (
            "Use o marcador __LACUNA__ no texto ou código para mostrar onde o aluno deve preencher."
        )
        self.fields["resposta_texto_codigo"].required = True
        if self.instance.pk and self.instance.respostas_aceitas:
            self.initial["respostas_aceitas"] = "\n".join(
                self.instance.respostas_aceitas
            )

    def clean_respostas_aceitas(self):
        respostas = self.cleaned_data["respostas_aceitas"].splitlines()
        return list(dict.fromkeys(resposta.strip() for resposta in respostas if resposta.strip()))


class ExercicioVerdadeiroFalsoForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = BASE_EXERCICIO_FIELDS + [
            "tipo",
            "resposta_vf_correta",  # O enunciado já está em BASE_EXERCICIO_FIELDS
        ]
        widgets = {
            **COMMON_WIDGETS,
            "enunciado": forms.Textarea(
                attrs={
                    "rows": 4,
                    "cols": 60,
                    "placeholder": "Digite a afirmação que o aluno deverá julgar como Verdadeira ou Falsa.",
                }
            ),
            "tipo": forms.HiddenInput(),
            "resposta_vf_correta": forms.RadioSelect(
                choices=[(True, "Verdadeiro"), (False, "Falso")]
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Novo exercício
            self.fields["tipo"].initial = "vf"
        elif self.instance.pk and self.instance.tipo == "vf":
            self.fields["tipo"].disabled = True

        # O campo 'enunciado' já é tratado pelo widget e sua obrigatoriedade
        # é definida no modelo (se blank=False).
        # Tornar a seleção de Verdadeiro/Falso obrigatória.
        # Para BooleanField com RadioSelect, null=False no modelo ou required=True no form garante isso.
        self.fields["resposta_vf_correta"].required = True
