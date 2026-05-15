from django.urls import path
from django.views.generic import RedirectView
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
    # Redirect slug alternativo → fluxo dedicado
    path('servico/certidao-de-procuracao-1/', RedirectView.as_view(pattern_name='pages:certidao_procuracao', permanent=False), name='certidao_procuracao_1_redirect'),
    # Imóvel
    path('servico/certidao-de-imovel/', views.CertidaoImovelView.as_view(), name='certidao_imovel'),
    path('servico/certidao-de-imovel/tipo/', views.CertidaoImovelTipoView.as_view(), name='certidao_imovel_tipo'),
    path('servico/certidao-de-imovel/formulario/', views.CertidaoImovelDadosView.as_view(), name='certidao_imovel_dados'),
    # Penhor de Safra
    path('servico/certidao-de-penhor-de-safra/', views.CertidaoPenhorSafraView.as_view(), name='certidao_penhor_safra'),
    path('servico/certidao-de-penhor-de-safra/dados/', views.CertidaoPenhorSafraDadosView.as_view(), name='certidao_penhor_safra_dados'),
    # Escritura
    path('servico/certidao-de-escritura/', views.CertidaoEscrituraView.as_view(), name='certidao_escritura'),
    path('servico/certidao-de-escritura/dados/', views.CertidaoEscrituraDadosView.as_view(), name='certidao_escritura_dados'),
    # Escritura de União Estável
    path('servico/certidao-de-escritura-de-uniao-estavel/', views.CertidaoUniaoEstavelView.as_view(), name='certidao_uniao_estavel'),
    path('servico/certidao-de-escritura-de-uniao-estavel/dados/', views.CertidaoUniaoEstavelDadosView.as_view(), name='certidao_uniao_estavel_dados'),
    # Escritura — Ata Notarial
    path('servico/certidao-de-escritura-de-ata-notarial/', views.CertidaoEscrituraAtaNotarialView.as_view(), name='certidao_escritura_ata_notarial'),
    path('servico/certidao-de-escritura-de-ata-notarial/dados/', views.CertidaoEscrituraAtaNotarialDadosView.as_view(), name='certidao_escritura_ata_notarial_dados'),
    # Escritura — Compra e Venda
    path('servico/certidao-de-escritura-de-compra-e-venda/', views.CertidaoEscrituraCompraVendaView.as_view(), name='certidao_escritura_compra_venda'),
    path('servico/certidao-de-escritura-de-compra-e-venda/dados/', views.CertidaoEscrituraCompraVendaDadosView.as_view(), name='certidao_escritura_compra_venda_dados'),
    # Escritura — Divórcio
    path('servico/certidao-de-escritura-de-divorcio/', views.CertidaoEscrituraDivorcioView.as_view(), name='certidao_escritura_divorcio'),
    path('servico/certidao-de-escritura-de-divorcio/dados/', views.CertidaoEscrituraDivorcioDadosView.as_view(), name='certidao_escritura_divorcio_dados'),
    # Escritura — Doação
    path('servico/certidao-de-escritura-de-doacao/', views.CertidaoEscrituraDoacaoView.as_view(), name='certidao_escritura_doacao'),
    path('servico/certidao-de-escritura-de-doacao/dados/', views.CertidaoEscrituraDoacaoDadosView.as_view(), name='certidao_escritura_doacao_dados'),
    # Escritura — Emancipação
    path('servico/certidao-de-escritura-de-emancipacao/', views.CertidaoEscrituraEmancipacaoView.as_view(), name='certidao_escritura_emancipacao'),
    path('servico/certidao-de-escritura-de-emancipacao/dados/', views.CertidaoEscrituraEmancipacaoDadosView.as_view(), name='certidao_escritura_emancipacao_dados'),
    # Escritura — Hipoteca
    path('servico/certidao-de-escritura-de-hipoteca/', views.CertidaoEscrituraHipotecaView.as_view(), name='certidao_escritura_hipoteca'),
    path('servico/certidao-de-escritura-de-hipoteca/dados/', views.CertidaoEscrituraHipotecaDadosView.as_view(), name='certidao_escritura_hipoteca_dados'),
    # Escritura — Inventário
    path('servico/certidao-de-escritura-de-inventario/', views.CertidaoEscrituraInventarioView.as_view(), name='certidao_escritura_inventario'),
    path('servico/certidao-de-escritura-de-inventario/dados/', views.CertidaoEscrituraInventarioDadosView.as_view(), name='certidao_escritura_inventario_dados'),
    # Escritura — Pacto Antenupcial
    path('servico/certidao-de-escritura-de-pacto-antenupcial/', views.CertidaoEscrituraPactoAntenupcialView.as_view(), name='certidao_escritura_pacto_antenupcial'),
    path('servico/certidao-de-escritura-de-pacto-antenupcial/dados/', views.CertidaoEscrituraPactoAntenupcialDadosView.as_view(), name='certidao_escritura_pacto_antenupcial_dados'),
    # Escritura — Permuta
    path('servico/certidao-de-escritura-de-permuta/', views.CertidaoEscrituraPermutaView.as_view(), name='certidao_escritura_permuta'),
    path('servico/certidao-de-escritura-de-permuta/dados/', views.CertidaoEscrituraPermutaDadosView.as_view(), name='certidao_escritura_permuta_dados'),
    # Escritura — Testamento
    path('servico/certidao-de-escritura-de-testamento/', views.CertidaoEscrituraTestamentoView.as_view(), name='certidao_escritura_testamento'),
    path('servico/certidao-de-escritura-de-testamento/dados/', views.CertidaoEscrituraTestamentoDadosView.as_view(), name='certidao_escritura_testamento_dados'),
    # Pacote de Certidões — Compra e Venda de Imóvel
    path('servico/pacote-de-certidoes-compra-e-venda-de-imovel/', views.PacoteCertidoesCompraVendaView.as_view(), name='pacote_certidoes_compra_venda'),
    path('servico/pacote-de-certidoes-compra-e-venda-de-imovel/dados/', views.PacoteCertidoesCompraVendaDadosView.as_view(), name='pacote_certidoes_compra_venda_dados'),
    # Variantes de Registro de Imóveis
    path('servico/certidao-negativa-de-alienacao-fiduciaria/', views.CertidaoAlienacaoFiduciariaView.as_view(), name='certidao_alienacao_fiduciaria'),
    path('servico/certidao-negativa-de-alienacao-fiduciaria/dados/', views.CertidaoAlienacaoFiduciariaDadosView.as_view(), name='certidao_alienacao_fiduciaria_dados'),
    path('servico/certidao-de-matricula-atualizada/', views.CertidaoMatriculaAtualizadaView.as_view(), name='certidao_matricula_atualizada'),
    path('servico/certidao-de-matricula-atualizada/dados/', views.CertidaoMatriculaAtualizadaDadosView.as_view(), name='certidao_matricula_atualizada_dados'),
    path('servico/certidao-de-onus-reais/', views.CertidaoOnusReaisView.as_view(), name='certidao_onus_reais'),
    path('servico/certidao-de-onus-reais/dados/', views.CertidaoOnusReaisDadosView.as_view(), name='certidao_onus_reais_dados'),
    path('servico/pesquisa-de-bens/', views.PesquisaBensView.as_view(), name='pesquisa_bens'),
    path('servico/pesquisa-de-bens/dados/', views.PesquisaBensDadosView.as_view(), name='pesquisa_bens_dados'),
    # Protestos
    path('servico/certidao-de-protesto/', views.CertidaoProtestoView.as_view(), name='certidao_protesto'),
    path('servico/pesquisa-de-protesto-nacional/', views.PesquisaProtestoNacionalView.as_view(), name='pesquisa_protesto_nacional'),
    # Federais e Estaduais
    path('servico/cnd-federal-receita-federal/', views.CndFederalView.as_view(), name='cnd_federal'),
    path('servico/certidao-fgts-inss/', views.CertidaoFgtsInssView.as_view(), name='certidao_fgts_inss'),
    path('servico/cadastro-de-imoveis-rurais-cafir/', views.CafirView.as_view(), name='cafir'),
    path('servico/certidao-ibama-certidao-de-embargos/', views.CertidaoIbamaEmbargosView.as_view(), name='certidao_ibama_embargos'),
    path('servico/cnd-estadual-sefaz/', views.CndEstadualView.as_view(), name='cnd_estadual'),
    path('servico/cnd-itr-receita-federal/', views.CndItrReceitaFederalView.as_view(), name='cnd_itr'),
    path('servico/cnj-improbidade-administrativa-e-inelegibilidade/', views.CnjImprobidadeAdministrativaView.as_view(), name='cnj_improbidade'),
    path('servico/certidao-negativa-de-acoes-criminais/', views.CertidaoNegativaAcoesCriminaisView.as_view(), name='certidao_negativa_acoes_criminais'),
    path('servico/certidao-negativa-de-debitos-ambientais/', views.CertidaoNegativaDebitosAmbientaisView.as_view(), name='certidao_negativa_debitos_ambientais'),
    path('servico/certidao-negativa-municipio/', views.CertidaoNegativaMunicipioView.as_view(), name='certidao_negativa_municipio'),
    path('servico/certidao-de-cumprimento-da-cota-legal-de-pcds/', views.CotaLegalPcdsView.as_view(), name='certidao_cota_legal_pcds'),
    path('servico/certidao-negativa-de-debitos-trabalhistas/', views.DebitosTrabalhalistasView.as_view(), name='certidao_debitos_trabalhistas'),
    path('servico/certidao-de-propriedade-de-aeronave/', views.PropriedadeAeronaveView.as_view(), name='certidao_propriedade_aeronave'),
    path('servico/junta-comercial-certidao-da-empresa/', views.JuntaComercialCertidaoEmpresaView.as_view(), name='junta_comercial_certidao_empresa'),
    path('servico/certidao-regularidade-crea/', views.CertidaoRegularidadeCreView.as_view(), name='certidao_regularidade_crea'),
    path('servico/certidao-antecedentes-criminais/', views.CertidaoAntecedentesCriminaisView.as_view(), name='certidao_antecedentes_criminais'),
    path('servico/tse-certidao-de-quitacao-eleitoral/', views.TseQuitacaoEleitoralView.as_view(), name='tse_quitacao_eleitoral'),
    # Busca em Cartorios
    path('servico/busca-em-cartorios-registro-civil/', views.BuscaCartorioRegistroCivilView.as_view(), name='busca_cartorios_civil'),
    path('servico/busca-em-tabelionatos-notas/', views.BuscaTabelionatoNotasView.as_view(), name='busca_tabelionatos_notas'),
    # Apostilamento
    path('servico/apostila-de-haia/', views.ApostilaHaiaView.as_view(), name='apostila_haia'),
    path('servico/traducao-juramentada/', views.TraducaoJuramentadaView.as_view(), name='traducao_juramentada'),
    path('api/cidades/', cidades_por_estado, name='cidades_por_estado'),
    path('quem-somos/', views.AboutView.as_view(), name='about'),
    path('fale-conosco/', views.ContactView.as_view(), name='contact'),
    path('termos-de-uso/', views.TermsView.as_view(), name='terms'),
    path('politica-de-privacidade/', views.PrivacyView.as_view(), name='privacy'),
    path('ressalva-legal/', views.LegalView.as_view(), name='legal'),
]
