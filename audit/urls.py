from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('historico/', views.HistoricoView.as_view(), name='historico'),
    path('historico/<int:pk>/', views.AtividadeDetalheView.as_view(), name='detalhe'),
]
