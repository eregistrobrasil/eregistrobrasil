from django.urls import path
from django.http import JsonResponse
from django.conf import settings
import json, os
from . import views

app_name = 'pages'


def cidades_por_estado(request):
    uf = request.GET.get('uf', '').upper()
    json_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'estados_cidades.json')
    with open(json_path, encoding='utf-8') as f:
        dados = json.load(f)
    cidades = dados.get(uf, {}).get('cidades', [])
    return JsonResponse({'cidades': cidades})


urlpatterns = [
    path('servico/certidao-de-nascimento-2a-via/', views.CertidaoNascimentoView.as_view(), name='certidao_nascimento'),
    path('servico/certidao-de-nascimento-2a-via/dados/', views.CertidaoDadosView.as_view(), name='certidao_nascimento_dados'),
    # Óbito
    path('servico/certidao-de-obito-2a-via/', views.CertidaoObitoView.as_view(), name='certidao_obito'),
    path('servico/certidao-de-obito-2a-via/dados/', views.CertidaoObitoDadosView.as_view(), name='certidao_obito_dados'),
    # Casamento
    path('servico/certidao-de-casamento-2a-via/', views.CertidaoCasamentoView.as_view(), name='certidao_casamento'),
    path('servico/certidao-de-casamento-2a-via/dados/', views.CertidaoCasamentoDadosView.as_view(), name='certidao_casamento_dados'),
    # Interdição
    path('servico/certidao-de-interdicao/', views.CertidaoInterdicaoView.as_view(), name='certidao_interdicao'),
    path('servico/certidao-de-interdicao/dados/', views.CertidaoInterdicaoDadosView.as_view(), name='certidao_interdicao_dados'),
    # Procuração
    path('servico/certidao-de-procuracao/', views.CertidaoProcuracaoView.as_view(), name='certidao_procuracao'),
    path('servico/certidao-de-procuracao/dados/', views.CertidaoProcuracaoDadosView.as_view(), name='certidao_procuracao_dados'),
    path('api/cidades/', cidades_por_estado, name='cidades_por_estado'),
    path('quem-somos/', views.AboutView.as_view(), name='about'),
    path('fale-conosco/', views.ContactView.as_view(), name='contact'),
    path('termos-de-uso/', views.TermsView.as_view(), name='terms'),
    path('politica-de-privacidade/', views.PrivacyView.as_view(), name='privacy'),
    path('ressalva-legal/', views.LegalView.as_view(), name='legal'),
]
