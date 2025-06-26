from django.contrib import admin
from django import forms
from .models import Ativado, Desativado, Tecnico , Categoria

@admin.register(Tecnico)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "sobrenome")
    search_fields = ("nome", "sobrenome")

@admin.register(Ativado)
class AtivadoAdmin(admin.ModelAdmin):
    list_display = ("nome", "sobrenome", "data_ativacao")
    search_fields = ("nome", "sobrenome")
    filter_horizontal = ("tecnicos",)

class DesativadoForm(forms.ModelForm):
    class Meta:
        model = Desativado
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.ativado:
            self.fields['nome'].initial = self.instance.ativado.nome  # Preenche automaticamente o nome

class DesativadoAdmin(admin.ModelAdmin):
    form = DesativadoForm
    list_display = ('nome', 'ativado', 'motivo', 'data_desativacao', 'equipamento_retirado')
    search_fields = ("nome", "motivo")
    autocomplete_fields = ['ativado']  # Facilita a busca por ativados no admin

    def save_model(self, request, obj, form, change):
        if obj.ativado:  # Agora sempre atualiza o nome
            obj.nome = f"{obj.ativado.nome} {obj.ativado.sobrenome}"
        super().save_model(request, obj, form, change)

admin.site.register(Desativado, DesativadoAdmin)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome",)