"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from products.api_views import (
    CategoriaListAPIView,
    TipoServicoListAPIView,
    ServicoListAPIView,
    ServicoDetailAPIView,
    ServicePriceByStateView,
    ImovelPriceByStateView,
)

admin.site.site_header = 'E-Registro Brasil — Administração'
admin.site.site_title = 'E-Registro Brasil'
admin.site.index_title = 'Painel Administrativo'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    path('', include('products.urls')),
    path('conta/', include('accounts.urls')),
    path('pedidos/', include('orders.urls')),
    path('pagamentos/', include('payments.urls')),
    path('blog/', include('blog.urls')),
    path('painel/', include('dashboard.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('documentos/', include('documents.urls')),
    # API pública de serviços
    path('api/categorias/', CategoriaListAPIView.as_view(), name='api-categorias'),
    path('api/tipos/', TipoServicoListAPIView.as_view(), name='api-tipos'),
    path('api/servicos/', ServicoListAPIView.as_view(), name='api-servicos'),
    path('api/servicos/<slug:slug>/', ServicoDetailAPIView.as_view(), name='api-servico-detail'),
    path('api/preco/', ServicePriceByStateView.as_view(), name='api-preco-estado'),
    path('api/preco-imovel/', ImovelPriceByStateView.as_view(), name='api-preco-imovel'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
