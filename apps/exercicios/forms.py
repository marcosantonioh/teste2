from django import forms

class SubmissaoForm(forms.Form):
    resposta = forms.CharField(widget=forms.Textarea, label="Sua Resposta")
