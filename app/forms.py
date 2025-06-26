from django import forms
from .models import Ativado, Tecnico

class LoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput)


class AtivadoForm(forms.ModelForm):
    class Meta:
        model = Ativado
        fields = ['nome', 'sobrenome', 'tecnicos', 'taxa', 'empresa', 'tecnologia', 'isento']