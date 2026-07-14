from django.contrib import admin
from .models import (
    PriceHistory, StatePriceHistory,
    ContaContabil, Lancamento, ServicoContaReceita,
)


@admin.register(ContaContabil)
class ContaContabilAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'tipo', 'natureza', 'parent', 'is_active', 'is_system')
    list_filter = ('tipo', 'natureza', 'is_active')
    search_fields = ('codigo', 'nome', 'descricao')
    ordering = ('codigo',)


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ('data_competencia', 'tipo', 'conta', 'descricao', 'valor', 'status', 'origem', 'order')
    list_filter = ('tipo', 'status', 'origem', 'forma_pagamento')
    search_fields = ('descricao', 'observacoes')
    date_hierarchy = 'data_competencia'
    autocomplete_fields = ('conta', 'order')
    ordering = ('-data_competencia',)


@admin.register(ServicoContaReceita)
class ServicoContaReceitaAdmin(admin.ModelAdmin):
    list_display = ('service', 'conta', 'updated_at')
    list_filter = ('conta',)
    search_fields = ('service__name', 'conta__nome', 'conta__codigo')


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
