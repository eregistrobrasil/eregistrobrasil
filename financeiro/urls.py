from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('', views.FinanceiroDashboardView.as_view(), name='dashboard'),
    path('servicos/', views.ServicoListView.as_view(), name='servicos'),
    path('servicos/novo/', views.ServicoCreateView.as_view(), name='servico_create'),
    path('servicos/<int:pk>/editar/', views.ServicoEditView.as_view(), name='servico_edit'),
    path('servicos/<int:pk>/excluir/', views.ServicoDeleteView.as_view(), name='servico_delete'),
    path('servicos/<int:pk>/preco/', views.PriceInlineUpdateView.as_view(), name='preco_update'),
    path('servicos/<int:pk>/toggle/', views.ServicoToggleAtivoView.as_view(), name='servico_toggle'),
    # Preços por estado
    path('servicos/estado/<int:pk>/preco/', views.StatePriceInlineUpdateView.as_view(), name='estado_preco_update'),
    path('servicos/estado/<int:pk>/toggle/', views.StatePriceToggleView.as_view(), name='estado_toggle'),
    path('servicos/bulk-preco/', views.BulkPriceUpdateView.as_view(), name='bulk_preco'),
    path('relatorios/', views.RelatorioView.as_view(), name='relatorios'),
]
