from django.contrib import admin
from .models import PriceHistory


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'preco_anterior', 'preco_novo', 'alterado_por', 'created_at')
    list_filter = ('product__category',)
    readonly_fields = ('product', 'preco_anterior', 'preco_novo', 'alterado_por', 'created_at')
    ordering = ('-created_at',)
