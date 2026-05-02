from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardIndexView.as_view(), name='index'),
    path('kanban/', views.KanbanView.as_view(), name='kanban'),
    path('pedidos/', views.OrderOpsListView.as_view(), name='order_list'),
    path('pedidos/<uuid:pk>/', views.OrderOpsDetailView.as_view(), name='order_detail'),
    path('pedidos/<uuid:pk>/status/', views.AlterarStatusView.as_view(), name='alterar_status'),
    path('pedidos/<uuid:pk>/responsavel/', views.AtribuirResponsavelView.as_view(), name='atribuir_responsavel'),
    path('kanban/mover/', views.KanbanMoverView.as_view(), name='kanban_mover'),
    path('notificacoes/', views.NotificacoesView.as_view(), name='notificacoes'),
]
