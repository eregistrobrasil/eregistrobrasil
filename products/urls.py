from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('busca/', views.SearchView.as_view(), name='search'),
    path('categoria/<slug:slug>/', views.CategoryDetailView.as_view(), name='category'),
    path('servico/<slug:slug>/', views.ProductDetailView.as_view(), name='detail'),
]
