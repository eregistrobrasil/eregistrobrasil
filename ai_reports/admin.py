from django.contrib import admin
from .models import DailyUserReport


@admin.register(DailyUserReport)
class DailyUserReportAdmin(admin.ModelAdmin):
    list_display = ('data', 'usuario', 'score_produtividade', 'total_acoes', 'criado_em')
    list_filter = ('data',)
    search_fields = ('usuario__email', 'usuario__first_name', 'resumo')
    readonly_fields = (
        'usuario', 'data', 'resumo', 'indicadores', 'recomendacoes',
        'alertas', 'score_produtividade', 'total_acoes',
        'modulos_acessados', 'criado_em', 'atualizado_em',
    )
    ordering = ('-data',)

    def has_add_permission(self, request):
        return False
