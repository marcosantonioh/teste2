from django import forms
from django.contrib.auth.models import User
from .models import Perfil


class LinksPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ('link_site', 'link_github', 'link_linkedin')

    def clean(self):
        dados = super().clean()
        for campo in self.Meta.fields:
            url = dados.get(campo)
            if url and not url.startswith('https://'):
                self.add_error(campo, 'Use um endereço HTTPS.')
        return dados


class CadastroUsuarioForm(forms.Form):
    """Valida os dados obrigatórios antes de criar um novo usuário."""

    username = forms.CharField(
        max_length=User._meta.get_field('username').max_length,
        strip=True,
        error_messages={'required': 'Informe seu nome.'},
    )
    email = forms.EmailField(
        error_messages={
            'required': 'Informe seu e-mail.',
            'invalid': 'Informe um endereço de e-mail válido.',
        },
    )
    password = forms.CharField(
        strip=False,
        error_messages={'required': 'Informe uma senha.'},
    )
    password2 = forms.CharField(
        strip=False,
        error_messages={'required': 'Confirme sua senha.'},
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                'Nome de usuário já está em uso. Escolha outro.'
            )
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password and password2 and password != password2:
            self.add_error('password2', 'As senhas não coincidem.')

        return cleaned_data
