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
    # Blog
    path('blog/', views.BlogListView.as_view(), name='blog_list'),
    path('blog/novo/', views.BlogCreateView.as_view(), name='blog_create'),
    path('blog/<int:pk>/editar/', views.BlogEditView.as_view(), name='blog_edit'),
    path('blog/<int:pk>/excluir/', views.BlogDeleteView.as_view(), name='blog_delete'),
    path('blog/<int:pk>/publicar/', views.BlogTogglePublishView.as_view(), name='blog_toggle_publish'),
    # Cartórios
    path('cartorios/', views.CartorioListView.as_view(), name='cartorio_list'),
    path('cartorios/novo/', views.CartorioCreateView.as_view(), name='cartorio_create'),
    path('cartorios/<int:pk>/editar/', views.CartorioEditView.as_view(), name='cartorio_edit'),
    path('cartorios/<int:pk>/excluir/', views.CartorioDeleteView.as_view(), name='cartorio_delete'),
    path('cartorios/<int:pk>/ativar/', views.CartorioToggleAtivoView.as_view(), name='cartorio_toggle_ativo'),
]
