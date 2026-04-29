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
    path('api/cidades/', cidades_por_estado, name='cidades_por_estado'),
    path('quem-somos/', views.AboutView.as_view(), name='about'),
    path('fale-conosco/', views.ContactView.as_view(), name='contact'),
    path('termos-de-uso/', views.TermsView.as_view(), name='terms'),
    path('politica-de-privacidade/', views.PrivacyView.as_view(), name='privacy'),
    path('ressalva-legal/', views.LegalView.as_view(), name='legal'),
]
