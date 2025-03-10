from django import forms
from django.contrib.auth.models import User

class CadastroForm(forms.ModelForm):
    senha = forms.CharField(widget=forms.PasswordInput)
    confirmar_senha = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email", "senha"]

    def clean(self):
        dados = super().clean()
        senha = dados.get("senha")
        confirmar_senha = dados.get("confirmar_senha")
        if senha != confirmar_senha:
            raise forms.ValidationError("As senhas não coincidem!")
        return dados