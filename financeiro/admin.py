from django.contrib import admin
from .models import PriceHistory, StatePriceHistory


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'preco_anterior', 'preco_novo', 'alterado_por', 'created_at')
    list_filter = ('product__category',)
    readonly_fields = ('product', 'preco_anterior', 'preco_novo', 'alterado_por', 'created_at')
    ordering = ('-created_at',)


@admin.register(StatePriceHistory)
class StatePriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('service', 'state_code', 'preco_anterior', 'preco_novo', 'alterado_por', 'created_at')
    list_filter = ('state_code', 'service__category')
    search_fields = ('service__name', 'state_code', 'observacao')
    readonly_fields = (
        'service_state_price', 'service', 'state_code',
        'preco_anterior', 'preco_novo', 'alterado_por', 'created_at',
    )
    ordering = ('-created_at',)
