from django.contrib import admin
from .models import UserActivity


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'usuario', 'acao', 'modulo', 'url', 'status', 'ip')
    list_filter = ('acao', 'modulo', 'status', 'data_hora')
    search_fields = ('usuario__email', 'url', 'ip', 'descricao')
    readonly_fields = (
        'usuario', 'data_hora', 'acao', 'modulo', 'descricao',
        'ip', 'navegador', 'url', 'metodo_http', 'tempo_execucao',
        'status', 'objeto_afetado', 'id_objeto',
        'dados_anteriores', 'dados_novos', 'observacoes',
    )
    ordering = ('-data_hora',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
