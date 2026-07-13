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
from accounts.views import StaffLoginView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from products.api_views import (
    CategoriaListAPIView,
    TipoServicoListAPIView,
    ServicoListAPIView,
    ServicoDetailAPIView,
    ServicePriceByStateView,
    ImovelPriceByStateView,
)
from registry.views import CartorioAPIView
from blog.sitemaps import BlogPostSitemap

admin.site.site_header = 'E-Registro Brasil LTDA — Administração'
admin.site.site_title = 'E-Registro Brasil LTDA'
admin.site.index_title = 'Painel Administrativo'

_sitemaps = {
    'blog': BlogPostSitemap,
}


def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        'Allow: /blog/',
        'Disallow: /painel/',
        'Disallow: /admin/',
        'Disallow: /conta/',
        'Disallow: /pedidos/',
        'Disallow: /pagamentos/',
        f'Sitemap: {request.build_absolute_uri("/sitemap.xml")}',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('stafflogin', StaffLoginView.as_view(), name='staff_login'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': _sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('', include('pages.urls')),
    path('', include('products.urls')),
    path('conta/', include('accounts.urls')),
    path('pedidos/', include('orders.urls')),
    path('pagamentos/', include('payments.urls')),
    path('blog/', include('blog.urls')),
    path('painel/', include('dashboard.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('documentos/', include('documents.urls')),
    path('auditoria/', include('audit.urls')),
    path('painel/relatorios-ia/', include('ai_reports.urls')),
    # API pública de serviços
    path('api/categorias/', CategoriaListAPIView.as_view(), name='api-categorias'),
    path('api/tipos/', TipoServicoListAPIView.as_view(), name='api-tipos'),
    path('api/servicos/', ServicoListAPIView.as_view(), name='api-servicos'),
    path('api/servicos/<slug:slug>/', ServicoDetailAPIView.as_view(), name='api-servico-detail'),
    path('api/preco/', ServicePriceByStateView.as_view(), name='api-preco-estado'),
    path('api/preco-imovel/', ImovelPriceByStateView.as_view(), name='api-preco-imovel'),
    path('api/cartorios/', CartorioAPIView.as_view(), name='api-cartorios'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
