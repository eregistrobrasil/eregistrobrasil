from django.contrib import admin
from .models import Registry


@admin.register(Registry)
class RegistryAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade', 'estado', 'tipo_servico', 'telefone', 'ativo')
    list_filter = ('estado', 'ativo')
    search_fields = ('nome', 'cidade', 'cnpj')
    list_editable = ('ativo',)
