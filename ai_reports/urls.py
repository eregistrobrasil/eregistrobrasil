from django.urls import path
from . import views

app_name = 'ai_reports'

urlpatterns = [
    path('', views.RelatoriosDashboardView.as_view(), name='dashboard'),
    path('<int:pk>/', views.RelatorioDetalheView.as_view(), name='detalhe'),
    path('gerar/', views.GerarRelatorioManualView.as_view(), name='gerar_manual'),
]
