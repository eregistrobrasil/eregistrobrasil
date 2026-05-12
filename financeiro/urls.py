from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('', views.FinanceiroDashboardView.as_view(), name='dashboard'),

    # ── Serviços ────────────────────────────────────────────────────────────
    path('servicos/', views.ServicoListView.as_view(), name='servicos'),
    path('servicos/novo/', views.ServicoCreateView.as_view(), name='servico_create'),
    path('servicos/<int:pk>/editar/', views.ServicoEditView.as_view(), name='servico_edit'),
    path('servicos/<int:pk>/excluir/', views.ServicoDeleteView.as_view(), name='servico_delete'),
    path('servicos/<int:pk>/preco/', views.PriceInlineUpdateView.as_view(), name='preco_update'),
    path('servicos/<int:pk>/toggle/', views.ServicoToggleAtivoView.as_view(), name='servico_toggle'),
    # Preços por estado (legacy inline — mantidos para compatibilidade)
    path('servicos/estado/<int:pk>/preco/', views.StatePriceInlineUpdateView.as_view(), name='estado_preco_update'),
    path('servicos/estado/<int:pk>/toggle/', views.StatePriceToggleView.as_view(), name='estado_toggle'),
    path('servicos/bulk-preco/', views.BulkPriceUpdateView.as_view(), name='bulk_preco'),

    # ── Preços por Estado (módulo dedicado) ─────────────────────────────────
    path('precos/', views.PrecosListView.as_view(), name='precos'),
    path('precos/novo/', views.PrecoCreateView.as_view(), name='preco_criar'),
    path('precos/<int:pk>/editar/', views.PrecoEditView.as_view(), name='preco_editar'),
    path('precos/<int:pk>/excluir/', views.PrecoDeleteView.as_view(), name='preco_excluir'),
    path('precos/<int:pk>/toggle/', views.PrecoToggleView.as_view(), name='preco_toggle'),
    path('precos/<int:pk>/inline/', views.PrecoInlineUpdateView.as_view(), name='preco_inline'),
    path('precos/massa/', views.PrecosMassUpdateView.as_view(), name='precos_massa'),
    path('precos/replicar/', views.PrecosReplicarView.as_view(), name='precos_replicar'),
    path('precos/servico/<int:pk>/', views.PrecosServicoView.as_view(), name='precos_servico'),

    # ── Relatórios ──────────────────────────────────────────────────────────
    path('relatorios/', views.RelatorioView.as_view(), name='relatorios'),
]
