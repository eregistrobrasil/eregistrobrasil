from django.contrib import admin
from .models import Registry


@admin.register(Registry)
class RegistryAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade', 'estado', 'prazo_medio_dias', 'ativo')
    list_filter = ('estado', 'ativo')
    search_fields = ('nome', 'cidade', 'contato')
    list_editable = ('ativo', 'prazo_medio_dias')
