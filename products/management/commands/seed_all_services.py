"""
Management command: seed_all_services
======================================
Cria (ou atualiza) todas as categorias e serviços do sistema de forma idempotente.

Regras:
- Nunca duplica registros (usa get_or_create por slug).
- Marca todos como is_system_service=True.
- Serviços da categoria "Federais e Estaduais" são marcados com has_fixed_price=True.
- Execução segura em produção (idempotente).

Uso:
    python manage.py seed_all_services
    python manage.py seed_all_services --force   # atualiza campos mesmo se já existir
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.models import Category, Product, TipoServico
from products.services import criar_precos_para_todos_estados

# Slugs das variantes de Registro de Imóveis que usam ServiceStatePrice
# (igual ao registro-civil — gerenciados em /financeiro/precos/)
IMOVEIS_VARIANTES_SLUGS = [
    "certidao-de-matricula-atualizada",
    "certidao-de-onus-reais",
    "certidao-negativa-de-alienacao-fiduciaria",
    "pesquisa-de-bens",
]

# ─── Definição canônica de todos os serviços do sistema ───────────────────────
# Estrutura: cada entrada em CATEGORIES define uma categoria e seus serviços.
# Campos de serviço:
#   name           - nome exibido
#   slug           - URL slug (obrigatório e único)
#   short          - descrição curta
#   description    - descrição completa
#   price          - preço base (fallback / referência)
#   original_price - preço "de" riscado (opcional)
#   days           - prazo de entrega
#   featured       - destaque na home
#   tipo           - slug do TipoServico (opcional)
#   has_fixed_price- preço fixo R$ 49,90 (para federais/estaduais)
#   meta_title     - SEO title
#   meta_desc      - SEO description

CATEGORIES = [
    # ─── Registro Civil ───────────────────────────────────────────────────────
    {
        "name": "Registro Civil",
        "slug": "registro-civil",
        "order": 1,
        "icon_svg": (
            '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
            'd="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>'
        ),
        "services": [
            {
                "name": "Certidão de Nascimento 2ª Via",
                "slug": "certidao-de-nascimento-2a-via",
                "short": "Certidão de nascimento atualizada para uso em processos, casamentos e outros fins legais.",
                "description": (
                    "Solicite a 2ª via da certidão de nascimento com agilidade e segurança. "
                    "Localizamos o registro em qualquer cartório do Brasil e encaminhamos sua "
                    "solicitação para emissão pelo cartório competente, com validade legal plena. "
                    "Ideal para processos judiciais, casamentos, passaportes, mudança de nome e "
                    "outros fins oficiais."
                ),
                "price": "89.90",
                "original_price": "129.90",
                "days": 7,
                "featured": True,
                "meta_title": "Certidão de Nascimento 2ª Via Online — E-Registro Brasil",
                "meta_desc": (
                    "Solicite sua certidão de nascimento 2ª via online. "
                    "Rápido, seguro e com entrega em todo o Brasil."
                ),
            },
            {
                "name": "Certidão de Casamento 2ª Via",
                "slug": "certidao-de-casamento-2a-via",
                "short": "Segunda via da certidão de casamento com validade em todo território nacional.",
                "description": (
                    "Solicitamos a 2ª via da certidão de casamento diretamente junto ao cartório de "
                    "registro civil onde o matrimônio foi realizado. Válida para processos de "
                    "divórcio, inventário, passaporte, alteração de nome e outros fins legais."
                ),
                "price": "89.90",
                "original_price": "129.90",
                "days": 7,
                "featured": True,
                "meta_title": "Certidão de Casamento 2ª Via Online — E-Registro Brasil",
                "meta_desc": (
                    "Obtenha a 2ª via da certidão de casamento online. "
                    "Buscamos no cartório de origem e entregamos em todo o Brasil."
                ),
            },
            {
                "name": "Certidão de Óbito 2ª Via",
                "slug": "certidao-de-obito-2a-via",
                "short": "Certidão de óbito para fins de inventário, pensão ou outros processos legais.",
                "description": (
                    "Segunda via da certidão de óbito emitida pelo cartório de registro civil. "
                    "Indispensável para inventário, pensão por morte, cancelamento de CPF, "
                    "seguro de vida e outros procedimentos legais após o falecimento."
                ),
                "price": "89.90",
                "original_price": "129.90",
                "days": 7,
                "featured": True,
                "meta_title": "Certidão de Óbito 2ª Via Online — E-Registro Brasil",
                "meta_desc": (
                    "Solicite a 2ª via da certidão de óbito com praticidade. "
                    "Atendemos cartórios em todo o Brasil."
                ),
            },
            {
                "name": "Certidão de Interdição",
                "slug": "certidao-de-interdicao",
                "short": "Certidão de interdição registrada em cartório de registro civil.",
                "description": (
                    "Certidão que comprova a interdição judicial registrada no Cartório de Registro Civil. "
                    "Necessária para representação legal, tutela e curatela."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 10,
                "featured": False,
                "meta_title": "Certidão de Interdição Online — E-Registro Brasil",
                "meta_desc": (
                    "Solicite certidão de interdição do registro civil online. "
                    "Atendemos qualquer cartório do Brasil."
                ),
            },
        ],
    },
    # ─── Tabelionato de Notas ─────────────────────────────────────────────────
    {
        "name": "Notas",
        "slug": "notas",
        "order": 2,
        "icon_svg": (
            '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
            'd="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293'
            'l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>'
        ),
        "services": [
            {
                "name": "Certidão de Procuração",
                "slug": "certidao-de-procuracao",
                "short": "Localização e emissão de certidão de procuração lavrada em cartório de notas.",
                "description": (
                    "Certidão de procuração pública lavrada em cartório de notas. "
                    "Usada para comprovar poderes outorgados em atos jurídicos, transações "
                    "imobiliárias, representações legais e negócios comerciais."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Procuração Online — E-Registro Brasil",
                "meta_desc": "Solicite certidão de procuração pública em qualquer tabelionato do Brasil.",
            },
            {
                "name": "Certidão de Escritura",
                "slug": "certidao-de-escritura",
                "short": "Certidão de escritura pública para compra e venda, doação, inventário e outros.",
                "description": (
                    "Certidão de escritura pública lavrada em Tabelionato de Notas. "
                    "Abrange escrituras de compra e venda, doação, divórcio, inventário e demais atos notariais."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Escritura Online — E-Registro Brasil",
                "meta_desc": "Obtenha certidão de escritura pública do tabelionato de notas online.",
            },
            {
                "name": "Certidão de Escritura de União Estável",
                "slug": "certidao-de-escritura-de-uniao-estavel",
                "short": "Certidão da escritura pública de união estável lavrada em cartório de notas.",
                "description": (
                    "Certidão de escritura de união estável para fins legais, financeiros e administrativos. "
                    "Necessária para herança, financiamentos, benefícios previdenciários e outros."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de União Estável Online — E-Registro Brasil",
                "meta_desc": "Certidão de escritura de união estável online, rápido e seguro.",
            },
            {
                "name": "Certidão de Escritura de Ata Notarial",
                "slug": "certidao-de-escritura-de-ata-notarial",
                "short": "Certidão de ata notarial lavrada em cartório de notas para fins probatórios.",
                "description": (
                    "A ata notarial é instrumento de fé pública usado para comprovar fatos, "
                    "como o conteúdo de páginas da internet, e-mails, mensagens e outros elementos. "
                    "Nosso serviço obtém a certidão da ata em qualquer tabelionato do Brasil."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Ata Notarial Online — E-Registro Brasil",
                "meta_desc": "Solicite certidão de ata notarial em tabelionatos de todo o Brasil.",
            },
            {
                "name": "Certidão de Escritura de Compra e Venda",
                "slug": "certidao-de-escritura-de-compra-e-venda",
                "short": "Certidão de escritura de compra e venda de imóvel lavrada em tabelionato.",
                "description": (
                    "Certidão da escritura pública de compra e venda de bem imóvel, "
                    "necessária para registro no Cartório de Registro de Imóveis, "
                    "financiamentos e transferências de propriedade."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Escritura de Compra e Venda Online — E-Registro Brasil",
                "meta_desc": "Certidão de escritura de compra e venda de imóvel com agilidade.",
            },
            {
                "name": "Certidão de Escritura de Divórcio",
                "slug": "certidao-de-escritura-de-divorcio",
                "short": "Certidão de escritura de divórcio consensual lavrada em cartório.",
                "description": (
                    "Certidão da escritura pública de divórcio consensual realizado em tabelionato de notas. "
                    "Necessária para averbação no registro civil, cartório de imóveis e demais atos pós-divórcio."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Escritura de Divórcio Online — E-Registro Brasil",
                "meta_desc": "Obtenha certidão de escritura de divórcio extrajudicial online.",
            },
            {
                "name": "Certidão de Escritura de Doação",
                "slug": "certidao-de-escritura-de-doacao",
                "short": "Certidão de escritura de doação de imóvel ou bem registrada em cartório.",
                "description": (
                    "Certidão de escritura de doação para doações de bens imóveis, móveis e outros. "
                    "Indispensável para registro, transferência de titularidade e fins tributários."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Escritura de Doação Online — E-Registro Brasil",
                "meta_desc": "Solicite certidão de escritura de doação em qualquer tabelionato.",
            },
            {
                "name": "Certidão de Escritura de Emancipação",
                "slug": "certidao-de-escritura-de-emancipacao",
                "short": "Certidão de emancipação voluntária lavrada em cartório de notas.",
                "description": (
                    "Certidão de escritura de emancipação de menor, concedida pelos pais em cartório de notas. "
                    "Necessária para averbação no registro de nascimento."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Escritura de Emancipação Online — E-Registro Brasil",
                "meta_desc": "Certidão de emancipação voluntária lavrada em tabelionato de notas.",
            },
            {
                "name": "Certidão de Escritura de Hipoteca",
                "slug": "certidao-de-escritura-de-hipoteca",
                "short": "Certidão de escritura de hipoteca de imóvel registrada em tabelionato.",
                "description": (
                    "Certidão da escritura pública de hipoteca, necessária para financiamentos, "
                    "garantias em crédito e negócios imobiliários."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Escritura de Hipoteca Online — E-Registro Brasil",
                "meta_desc": "Solicite certidão de hipoteca de imóvel lavrada em cartório de notas.",
            },
            {
                "name": "Certidão de Escritura de Inventário",
                "slug": "certidao-de-escritura-de-inventario",
                "short": "Certidão de escritura de inventário e partilha extrajudicial.",
                "description": (
                    "Certidão de inventário e partilha extrajudicial realizado em tabelionato de notas, "
                    "para transferência de bens entre herdeiros sem necessidade de processo judicial."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Escritura de Inventário Online — E-Registro Brasil",
                "meta_desc": "Certidão de inventário extrajudicial lavrado em tabelionato de notas.",
            },
            {
                "name": "Certidão de Escritura de Pacto Antenupcial",
                "slug": "certidao-de-escritura-de-pacto-antenupcial",
                "short": "Certidão de pacto antenupcial lavrado em cartório de notas antes do casamento.",
                "description": (
                    "Certidão de pacto antenupcial que define o regime de bens do casal. "
                    "Necessária para averbação no Registro de Imóveis e no Registro Civil."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Pacto Antenupcial Online — E-Registro Brasil",
                "meta_desc": "Solicite certidão de pacto antenupcial lavrado em tabelionato.",
            },
            {
                "name": "Certidão de Escritura de Permuta",
                "slug": "certidao-de-escritura-de-permuta",
                "short": "Certidão de escritura de permuta (troca) de imóveis registrada em tabelionato.",
                "description": (
                    "Certidão de escritura de permuta entre bens imóveis, "
                    "necessária para o registro da transferência nos respectivos cartórios de imóveis."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Escritura de Permuta Online — E-Registro Brasil",
                "meta_desc": "Certidão de escritura de permuta de imóveis em qualquer tabelionato.",
            },
            {
                "name": "Certidão de Escritura de Testamento",
                "slug": "certidao-de-escritura-de-testamento",
                "short": "Certidão de testamento público lavrado em cartório de notas.",
                "description": (
                    "Certidão de testamento público registrado em Tabelionato de Notas. "
                    "Essencial para abertura de inventário, cumprimento de legados e disposições de última vontade."
                ),
                "price": "219.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Testamento Online — E-Registro Brasil",
                "meta_desc": "Solicite certidão de testamento público em tabelionato de notas.",
            },
        ],
    },
    # ─── Registro de Imóveis ──────────────────────────────────────────────────
    {
        "name": "Imóveis",
        "slug": "imoveis",
        "order": 3,
        "icon_svg": (
            '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
            'd="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3'
            'm-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>'
        ),
        "services": [
            {
                "name": "Certidão de Imóvel",
                "slug": "certidao-de-imovel",
                "short": "Certidão de imóvel: matrícula, ônus reais, vintenária, transcrição e mais.",
                "description": (
                    "Solicite certidões do Registro de Imóveis: matrícula atualizada, inteiro teor, "
                    "vintenária, transcrição, documentos arquivados, pacto antinupcial, condomínio, "
                    "livro 3 e quesitos. Atendemos cartórios em todo o Brasil."
                ),
                "price": "149.90",
                "original_price": "199.90",
                "days": 5,
                "featured": True,
                "meta_title": "Certidão de Imóvel Online — E-Registro Brasil",
                "meta_desc": (
                    "Certidões do Registro de Imóveis online: matrícula, ônus reais, vintenária e mais. "
                    "Rápido e seguro em todo o Brasil."
                ),
            },
            {
                "name": "Certidão de Penhor de Safra",
                "slug": "certidao-de-penhor-de-safra",
                "short": "Certidão de penhor de safra registrada no cartório de registro de imóveis.",
                "description": (
                    "Certidão de penhor de safra ou de gado, necessária para financiamentos rurais, "
                    "operações de crédito agrícola e garantias de empréstimos do agronegócio."
                ),
                "price": "149.90",
                "original_price": None,
                "days": 7,
                "featured": False,
                "meta_title": "Certidão de Penhor de Safra Online — E-Registro Brasil",
                "meta_desc": "Solicite certidão de penhor de safra do registro de imóveis online.",
            },
            {
                "name": "Pacote de Certidões — Compra e Venda de Imóvel",
                "slug": "pacote-de-certidoes-compra-e-venda-de-imovel",
                "short": "Pacote completo de certidões para compra e venda de imóvel.",
                "description": (
                    "Pacote completo com todas as certidões necessárias para compra e venda de imóvel: "
                    "matrícula atualizada, certidões dos proprietários (vendedores), certidão de ônus reais, "
                    "certidão municipal e outros documentos essenciais para a transação segura."
                ),
                "price": "399.90",
                "original_price": "549.90",
                "days": 7,
                "featured": True,
                "meta_title": "Pacote Certidões Compra e Venda de Imóvel — E-Registro Brasil",
                "meta_desc": "Pacote completo de certidões para compra e venda de imóvel com segurança.",
            },
            {
                "name": "Certidão de Matrícula Atualizada",
                "slug": "certidao-de-matricula-atualizada",
                "short": "Certidão atualizada com a situação jurídica atual do imóvel.",
                "description": (
                    "Solicite a certidão de matrícula atualizada do Cartório de Registro de Imóveis. "
                    "Documento que comprova titularidade, histórico de transmissões, ônus e ações ajuizadas."
                ),
                "price": "149.90",
                "original_price": None,
                "days": 5,
                "featured": False,
                "meta_title": "Certidão de Matrícula Atualizada Online — E-Registro Brasil",
                "meta_desc": "Certidão de matrícula atualizada do Registro de Imóveis online. Rápido e seguro.",
            },
            {
                "name": "Certidão de Ônus Reais",
                "slug": "certidao-de-onus-reais",
                "short": "Certidão de inteiro teor com todos os ônus e gravames do imóvel.",
                "description": (
                    "Certidão que lista hipotecas, penhoras, alienações fiduciárias e demais gravames "
                    "incidentes sobre o imóvel. Indispensável em financiamentos e transações imobiliárias."
                ),
                "price": "149.90",
                "original_price": None,
                "days": 5,
                "featured": False,
                "meta_title": "Certidão de Ônus Reais Online — E-Registro Brasil",
                "meta_desc": "Certidão de ônus reais do Registro de Imóveis online. Todos os gravames e hipotecas.",
            },
            {
                "name": "Certidão Negativa de Alienação Fiduciária",
                "slug": "certidao-negativa-de-alienacao-fiduciaria",
                "short": "Certidão que comprova inexistência de alienação fiduciária em nome do requerente.",
                "description": (
                    "Certidão negativa que atesta a inexistência de alienação fiduciária de bens imóveis "
                    "registrada em nome de pessoa física ou jurídica no Cartório de Registro de Imóveis."
                ),
                "price": "149.90",
                "original_price": None,
                "days": 5,
                "featured": False,
                "meta_title": "Certidão Negativa de Alienação Fiduciária Online — E-Registro Brasil",
                "meta_desc": "Certidão negativa de alienação fiduciária do Registro de Imóveis online.",
            },
            {
                "name": "Pesquisa de Bens",
                "slug": "pesquisa-de-bens",
                "short": "Pesquisa de bens imóveis registrados em nome de pessoa física ou jurídica.",
                "description": (
                    "Pesquisa ampla de bens imóveis registrados em nome de uma pessoa junto ao Cartório de "
                    "Registro de Imóveis. Utilizada em processos judiciais, planejamento patrimonial e "
                    "due diligence."
                ),
                "price": "149.90",
                "original_price": None,
                "days": 5,
                "featured": False,
                "meta_title": "Pesquisa de Bens Imóveis Online — E-Registro Brasil",
                "meta_desc": "Pesquisa de bens imóveis registrados em nome de pessoa no Registro de Imóveis.",
            },
        ],
    },
    # ─── Tabelionato de Protestos ─────────────────────────────────────────────
    {
        "name": "Protestos",
        "slug": "protestos",
        "order": 4,
        "icon_svg": (
            '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
            'd="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2'
            'M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>'
        ),
        "services": [
            {
                "name": "Certidão de Protesto",
                "slug": "certidao-de-protesto",
                "short": "Certidão negativa ou positiva de protestos em tabelionatos de protestos.",
                "description": (
                    "Certidão de protestos emitida pelo Tabelionato de Protestos. "
                    "Comprova a existência ou ausência de títulos protestados (cheques, notas promissórias, "
                    "duplicatas etc.) em nome de pessoa física ou jurídica. "
                    "Necessária para financiamentos, licitações e operações de crédito."
                ),
                "price": "79.90",
                "original_price": "99.90",
                "days": 3,
                "featured": False,
                "meta_title": "Certidão de Protesto Online — E-Registro Brasil",
                "meta_desc": "Solicite certidão de protesto de títulos em tabelionatos de todo o Brasil.",
            },
            {
                "name": "Busca de Protesto",
                "slug": "busca-de-protesto",
                "short": "Busca de protesto em cartório de protestos em todo o Brasil.",
                "description": (
                    "Busca de protesto de títulos em tabelionatos de protestos. "
                    "Verifica a existência de protestos em nome de pessoa física ou jurídica "
                    "em um cartório específico ou em toda a cidade informada."
                ),
                "price": "79.90",
                "original_price": "99.90",
                "days": 3,
                "featured": False,
                "meta_title": "Busca de Protesto Online — E-Registro Brasil",
                "meta_desc": "Solicite busca de protesto em tabelionatos de todo o Brasil com agilidade.",
            },
            {
                "name": "Pesquisa de Protesto Nacional",
                "slug": "pesquisa-de-protesto-nacional",
                "short": "Pesquisa nacional de protestos via sistema CRA para pessoa física ou jurídica.",
                "description": (
                    "Pesquisa de protestos em nível nacional através do sistema CRA (Central de Recuperação de Ativos). "
                    "Abrange todos os tabelionatos de protestos do Brasil. "
                    "Ideal para due diligence, operações de crédito e análise de risco."
                ),
                "price": "59.90",
                "original_price": "79.90",
                "days": 2,
                "featured": False,
                "meta_title": "Pesquisa de Protesto Nacional Online — E-Registro Brasil",
                "meta_desc": "Pesquisa nacional de protesto via CRA para PF e PJ. Rápido e online.",
            },
        ],
    },
    # ─── Federais e Estaduais (preço fixo R$ 49,90) ───────────────────────────
    {
        "name": "Federais e Estaduais",
        "slug": "federais-e-estaduais",
        "order": 5,
        "icon_svg": (
            '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
            'd="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5'
            'M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>'
        ),
        "services": [
            {
                "name": "CND Federal (Receita Federal)",
                "slug": "cnd-federal-receita-federal",
                "short": "Certidão Negativa de Débitos federais junto à Receita Federal.",
                "description": (
                    "Certidão Negativa de Débitos (CND) emitida pela Receita Federal do Brasil. "
                    "Comprova a regularidade fiscal de pessoa física ou jurídica perante a União. "
                    "Exigida para licitações, financiamentos, certidões negativas municipais e outros fins."
                ),
                "price": "49.90",
                "original_price": "69.90",
                "days": 1,
                "featured": False,
                "has_fixed_price": True,
                "meta_title": "CND Federal Receita Federal Online — E-Registro Brasil",
                "meta_desc": "Emita a CND Federal da Receita Federal online com agilidade. Apenas R$ 49,90.",
            },
            {
                "name": "Certidão FGTS / INSS",
                "slug": "certidao-fgts-inss",
                "short": "Certidão de Regularidade do FGTS para pessoa física ou jurídica.",
                "description": (
                    "Certidão de Regularidade do FGTS (CRF), emitida pela Caixa Econômica Federal, "
                    "e certidão de regularidade previdenciária (INSS). "
                    "Exigida em licitações, contratos com órgãos públicos e financiamentos."
                ),
                "price": "49.90",
                "original_price": "69.90",
                "days": 1,
                "featured": False,
                "has_fixed_price": True,
                "meta_title": "Certidão FGTS / INSS Online — E-Registro Brasil",
                "meta_desc": "Obtenha a Certidão de Regularidade do FGTS e INSS online. R$ 49,90.",
            },
            {
                "name": "CND Estadual (SEFAZ)",
                "slug": "cnd-estadual-sefaz",
                "short": "Certidão Negativa de Débitos estaduais para licitações e contratos.",
                "description": (
                    "Certidão Negativa de Débitos estaduais, emitida pela Secretaria de Fazenda (SEFAZ) "
                    "do estado de interesse. Indispensável para licitações estaduais, contratos com o governo "
                    "e operações de crédito que exijam regularidade perante o estado."
                ),
                "price": "49.90",
                "original_price": "69.90",
                "days": 1,
                "featured": False,
                "has_fixed_price": True,
                "meta_title": "CND Estadual SEFAZ Online — E-Registro Brasil",
                "meta_desc": "Certidão Negativa Estadual SEFAZ online. Rápido e seguro. R$ 49,90.",
            },
            {
                "name": "Certidão Negativa de Débitos Municipais",
                "slug": "certidao-negativa-municipio",
                "short": "Certidão de regularidade fiscal junto à Prefeitura do município.",
                "description": (
                    "Certidão Negativa de Débitos municipais emitida pela Prefeitura. "
                    "Necessária para participar de licitações, contratos e financiamentos municipais."
                ),
                "price": "49.90",
                "original_price": "69.90",
                "days": 1,
                "featured": False,
                "has_fixed_price": True,
                "meta_title": "Certidão Negativa Municipal Online — E-Registro Brasil",
                "meta_desc": "Certidão Negativa de Débitos Municipal online. R$ 49,90.",
            },
            {
                "name": "Certidão de Regularidade no CREA",
                "slug": "certidao-regularidade-crea",
                "short": "Certidão de regularidade profissional no CREA.",
                "description": (
                    "Certidão de Registro e Regularidade emitida pelo CREA (Conselho Regional de "
                    "Engenharia e Agronomia). Necessária para participação em licitações e comprovação "
                    "de habilitação técnica profissional."
                ),
                "price": "49.90",
                "original_price": "69.90",
                "days": 1,
                "featured": False,
                "has_fixed_price": True,
                "meta_title": "Certidão CREA Online — E-Registro Brasil",
                "meta_desc": "Solicite certidão de regularidade do CREA online. R$ 49,90.",
            },
            {
                "name": "Certidão de Antecedentes Criminais",
                "slug": "certidao-antecedentes-criminais",
                "short": "Certidão de antecedentes criminais da Polícia Federal e estaduais.",
                "description": (
                    "Certidão de antecedentes criminais emitida pela Polícia Federal e/ou delegacias estaduais. "
                    "Exigida em concursos públicos, processos seletivos, vistos, adoções e outros fins legais."
                ),
                "price": "49.90",
                "original_price": "69.90",
                "days": 1,
                "featured": False,
                "has_fixed_price": True,
                "meta_title": "Certidão de Antecedentes Criminais Online — E-Registro Brasil",
                "meta_desc": "Certidão de antecedentes criminais Polícia Federal online. R$ 49,90.",
            },
            {
                "name": "TSE — Certidão de Quitação Eleitoral",
                "slug": "tse-certidao-de-quitacao-eleitoral",
                "short": "Certidão que comprova a regularidade eleitoral perante a Justiça Eleitoral.",
                "description": (
                    "Certidão de Quitação Eleitoral emitida pelo Tribunal Superior Eleitoral (TSE). "
                    "Comprova que o eleitor está quite com a Justiça Eleitoral, sem débitos de multas ou "
                    "justificativas pendentes. Exigida para posse em cargos públicos, concursos, passaportes "
                    "e financiamentos."
                ),
                "price": "49.90",
                "original_price": "69.90",
                "days": 1,
                "featured": False,
                "has_fixed_price": True,
                "meta_title": "Certidão de Quitação Eleitoral TSE Online — E-Registro Brasil",
                "meta_desc": "Solicite a Certidão de Quitação Eleitoral do TSE online. R$ 49,90.",
            },
            {
                "name": "CND ITR — Receita Federal",
                "slug": "cnd-itr-receita-federal",
                "short": "Certidão Negativa de Débitos do Imposto Territorial Rural para imóveis rurais.",
                "description": (
                    "Certidão Negativa de Débitos do ITR (Imposto Territorial Rural), emitida pela Receita "
                    "Federal do Brasil. Exigida em transações imobiliárias rurais, concessão de crédito rural, "
                    "participação em licitações e regularização fundiária de imóveis no INCRA."
                ),
                "price": "49.90",
                "original_price": "69.90",
                "days": 1,
                "featured": False,
                "has_fixed_price": True,
                "meta_title": "CND ITR Receita Federal Online — E-Registro Brasil",
                "meta_desc": "Solicite a Certidão Negativa de Débitos do ITR online. R$ 49,90.",
            },
            {
                "name": "CNJ — Improbidade Administrativa e Inelegibilidade",
                "slug": "cnj-improbidade-administrativa-e-inelegibilidade",
                "short": "Certidão do CNJ sobre condenações por improbidade administrativa e inelegibilidade.",
                "description": (
                    "Certidão emitida pelo Conselho Nacional de Justiça (CNJ) que comprova a ausência de "
                    "condenações por atos de improbidade administrativa (Lei nº 8.429/1992) e inelegibilidade "
                    "(LC 64/1990). Indispensável para posse em cargos públicos, candidaturas, licitações e "
                    "credenciamentos junto à Administração Pública."
                ),
                "price": "49.90",
                "original_price": "69.90",
                "days": 1,
                "featured": False,
                "has_fixed_price": True,
                "meta_title": "Certidão CNJ Improbidade Administrativa Online — E-Registro Brasil",
                "meta_desc": "Solicite a certidão CNJ de improbidade administrativa e inelegibilidade online. R$ 49,90.",
            },
        ],
    },
    # ─── Busca em Cartórios ───────────────────────────────────────────────────
    {
        "name": "Busca",
        "slug": "busca",
        "order": 6,
        "icon_svg": (
            '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
            'd="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>'
        ),
        "services": [
            {
                "name": "Busca em Cartórios de Registro Civil",
                "slug": "busca-em-cartorios-registro-civil",
                "short": "Pesquisa ampla em cartórios de registro civil para localização de documentos.",
                "description": (
                    "Serviço de busca e localização de registros em Cartórios de Registro Civil do Brasil. "
                    "Ideal para quem não sabe em qual cartório o registro foi lavrado. "
                    "Nossa equipe pesquisa em múltiplos cartórios até encontrar o documento."
                ),
                "price": "89.90",
                "original_price": None,
                "days": 5,
                "featured": False,
                "meta_title": "Busca em Cartórios de Registro Civil — E-Registro Brasil",
                "meta_desc": "Localização de registros em cartórios de registro civil em todo o Brasil.",
            },
            {
                "name": "Busca em Tabelionatos de Notas",
                "slug": "busca-em-tabelionatos-notas",
                "short": "Pesquisa de escrituras, procurações e atos notariais em tabelionatos.",
                "description": (
                    "Pesquisa de escrituras públicas, procurações, testamentos e outros atos notariais "
                    "em Tabelionatos de Notas de qualquer município do Brasil. "
                    "Útil quando não há certeza sobre o cartório onde o ato foi praticado."
                ),
                "price": "89.90",
                "original_price": None,
                "days": 5,
                "featured": False,
                "meta_title": "Busca em Tabelionatos de Notas — E-Registro Brasil",
                "meta_desc": "Pesquisa de escrituras e procurações em tabelionatos de notas.",
            },
        ],
    },
    # ─── Apostilamento ────────────────────────────────────────────────────────
    {
        "name": "Apostilamento",
        "slug": "apostilamento",
        "order": 7,
        "icon_svg": (
            '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
            'd="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10'
            'M12.751 5C11.783 10.77 8.07 15.61 3 18.129"/></svg>'
        ),
        "services": [
            {
                "name": "Apostila de Haia",
                "slug": "apostila-de-haia",
                "short": "Apostilamento de documentos para reconhecimento nos países da Convenção de Haia.",
                "description": (
                    "A Apostila de Haia é o processo que legaliza documentos brasileiros para uso em países "
                    "signatários da Convenção de Haia, sem necessidade de reconhecimento consular. "
                    "Indispensável para visto, dupla cidadania, estudos e trabalho no exterior."
                ),
                "price": "199.90",
                "original_price": "249.90",
                "days": 7,
                "featured": True,
                "meta_title": "Apostila de Haia Online — E-Registro Brasil",
                "meta_desc": (
                    "Apostile seus documentos para uso internacional com a Apostila de Haia. "
                    "Rápido, seguro e online."
                ),
            },
            {
                "name": "Tradução Juramentada",
                "slug": "traducao-juramentada",
                "short": "Tradução juramentada por Tradutor Público registrado na Junta Comercial.",
                "description": (
                    "Tradução juramentada realizada por Tradutor Público Juramentado registrado na Junta Comercial, "
                    "com fé pública reconhecida em todo o território nacional. "
                    "Disponível para documentos em inglês, espanhol, francês, alemão, italiano e outros idiomas."
                ),
                "price": "350.00",
                "original_price": None,
                "days": 10,
                "featured": False,
                "meta_title": "Tradução Juramentada Online — E-Registro Brasil",
                "meta_desc": "Tradução juramentada por tradutor público para documentos oficiais.",
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Seed completo e idempotente de todas as categorias e serviços do sistema"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Atualiza campos de descrição, SEO e flags mesmo em serviços já existentes.',
        )

    def handle(self, *args, **options):
        force = options['force']
        total_cats = 0
        total_svcs = 0
        updated_svcs = 0

        for cat_data in CATEGORIES:
            cat_slug = cat_data['slug']
            category, cat_created = Category.objects.get_or_create(
                slug=cat_slug,
                defaults={
                    'name': cat_data['name'],
                    'icon_svg': cat_data.get('icon_svg', ''),
                    'order': cat_data.get('order', 0),
                    'is_active': True,
                },
            )
            if cat_created:
                total_cats += 1
                self.stdout.write(f'  [NOVA CATEGORIA] {category.name}')
            elif force:
                # Atualiza ícone e ordem se --force
                category.icon_svg = cat_data.get('icon_svg', category.icon_svg)
                category.order = cat_data.get('order', category.order)
                category.save(update_fields=['icon_svg', 'order'])

            for svc in cat_data.get('services', []):
                svc_slug = svc['slug']
                has_fixed = svc.get('has_fixed_price', False)
                defaults = {
                    'name': svc['name'],
                    'category': category,
                    'short_description': svc.get('short', ''),
                    'description': svc.get('description', svc.get('short', '')),
                    'price': Decimal(svc['price']),
                    'original_price': Decimal(svc['original_price']) if svc.get('original_price') else None,
                    'delivery_days': svc.get('days', 5),
                    'is_active': True,
                    'is_featured': svc.get('featured', False),
                    'is_system_service': True,
                    'has_fixed_price': has_fixed,
                    'meta_title': svc.get('meta_title', ''),
                    'meta_description': svc.get('meta_desc', ''),
                }
                product, svc_created = Product.objects.get_or_create(
                    slug=svc_slug,
                    defaults=defaults,
                )
                if svc_created:
                    total_svcs += 1
                    self.stdout.write(f'    + {product.name}')
                elif force:
                    # Atualiza apenas campos não-financeiros críticos via --force
                    for field in [
                        'name', 'category', 'short_description', 'description',
                        'is_system_service', 'has_fixed_price',
                        'meta_title', 'meta_description', 'is_active',
                    ]:
                        setattr(product, field, defaults[field])
                    product.save(update_fields=[
                        'name', 'category', 'short_description', 'description',
                        'is_system_service', 'has_fixed_price',
                        'meta_title', 'meta_description', 'is_active',
                    ])
                    updated_svcs += 1
                    self.stdout.write(f'    ~ {product.name} (atualizado)')

        # Marca serviços já existentes como is_system_service=True se ainda não estiver
        # (para sistemas que tinham produtos antes deste seed)
        slugs_sistema = [
            svc['slug']
            for cat in CATEGORIES
            for svc in cat.get('services', [])
        ]
        auto_marked = (
            Product.objects
            .filter(slug__in=slugs_sistema, is_system_service=False)
            .update(is_system_service=True)
        )
        if auto_marked:
            self.stdout.write(
                self.style.WARNING(
                    f'  {auto_marked} serviço(s) marcados como is_system_service=True retroativamente.'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSeed concluído: {total_cats} categoria(s) criada(s), '
                f'{total_svcs} serviço(s) criado(s), {updated_svcs} atualizado(s).'
            )
        )

        # Garante que os preços por estado (ServiceStatePrice) existam para as
        # variantes de Imóveis que usam a mesma tabela que registro-civil.
        # Idempotente: criar_precos_para_todos_estados usa get_or_create internamente.
        self.stdout.write('\nGarantindo ServiceStatePrice para variantes de Imóveis...')
        for slug in IMOVEIS_VARIANTES_SLUGS:
            try:
                product = Product.objects.get(slug=slug)
                from products.models import ServiceStatePrice, State
                existentes_antes = ServiceStatePrice.objects.filter(service=product).count()
                criar_precos_para_todos_estados(product)
                existentes_depois = ServiceStatePrice.objects.filter(service=product).count()
                criados = existentes_depois - existentes_antes
                if criados:
                    self.stdout.write(f'  + {slug}: {criados} estado(s) criado(s)')
                else:
                    self.stdout.write(f'  ~ {slug}: preços já existiam ({existentes_depois} estados)')
            except Product.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'  ! {slug}: produto não encontrado, pulando')
                )
