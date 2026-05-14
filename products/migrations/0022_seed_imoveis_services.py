# Generated — data migration
# Garante que TODOS os serviços da categoria Imóveis existam no banco.
# Idempotente: usa get_or_create por slug.
# Depende de: 0021_alter_product_has_fixed_price
#
# Este arquivo é a fonte-da-verdade para os serviços de imóveis.
# Em caso de conflito, os dados aqui definidos prevalecem via --force no seed.

from decimal import Decimal

from django.db import migrations

# ─── Catálogo canônico de serviços de Imóveis ────────────────────────────────
# Mantido em sincronia com seed_all_services.py.
# slug é a chave única — nunca alterá-lo sem criar uma migration de renomeação.

_CATEGORIA = {
    "name": "Imóveis",
    "slug": "imoveis",
    "order": 3,
    "icon_svg": (
        '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
        'd="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3'
        'm-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>'
    ),
}

_SERVICOS = [
    {
        "name": "Certidão de Imóvel",
        "slug": "certidao-de-imovel",
        "short_description": "Certidão de imóvel: matrícula, ônus reais, vintenária, transcrição e mais.",
        "description": (
            "Solicite certidões do Registro de Imóveis: matrícula atualizada, inteiro teor, "
            "vintenária, transcrição, documentos arquivados, pacto antinupcial, condomínio, "
            "livro 3 e quesitos. Atendemos cartórios em todo o Brasil."
        ),
        "price": Decimal("149.90"),
        "original_price": Decimal("199.90"),
        "delivery_days": 5,
        "is_featured": True,
        "is_system_service": True,
        "has_fixed_price": False,
        "order": 1,
        "meta_title": "Certidão de Imóvel Online — E-Registro Brasil",
        "meta_description": (
            "Certidões do Registro de Imóveis online: matrícula, ônus reais, vintenária e mais. "
            "Rápido e seguro em todo o Brasil."
        ),
    },
    {
        "name": "Certidão de Penhor de Safra",
        "slug": "certidao-de-penhor-de-safra",
        "short_description": "Certidão de penhor de safra registrada no cartório de registro de imóveis.",
        "description": (
            "Certidão de penhor de safra ou de gado, necessária para financiamentos rurais, "
            "operações de crédito agrícola e garantias de empréstimos do agronegócio."
        ),
        "price": Decimal("149.90"),
        "original_price": None,
        "delivery_days": 7,
        "is_featured": False,
        "is_system_service": True,
        "has_fixed_price": False,
        "order": 2,
        "meta_title": "Certidão de Penhor de Safra Online — E-Registro Brasil",
        "meta_description": "Solicite certidão de penhor de safra do registro de imóveis online.",
    },
    {
        "name": "Pacote de Certidões — Compra e Venda de Imóvel",
        "slug": "pacote-de-certidoes-compra-e-venda-de-imovel",
        "short_description": "Pacote completo de certidões para compra e venda de imóvel.",
        "description": (
            "Pacote completo com todas as certidões necessárias para compra e venda de imóvel: "
            "matrícula atualizada, certidões dos proprietários (vendedores), certidão de ônus reais, "
            "certidão municipal e outros documentos essenciais para a transação segura."
        ),
        "price": Decimal("399.90"),
        "original_price": Decimal("549.90"),
        "delivery_days": 7,
        "is_featured": True,
        "is_system_service": True,
        "has_fixed_price": False,
        "order": 3,
        "meta_title": "Pacote Certidões Compra e Venda de Imóvel — E-Registro Brasil",
        "meta_description": "Pacote completo de certidões para compra e venda de imóvel com segurança.",
    },
    {
        "name": "Certidão de Matrícula Atualizada",
        "slug": "certidao-de-matricula-atualizada",
        "short_description": "Certidão atualizada com a situação jurídica atual do imóvel.",
        "description": (
            "Solicite a certidão de matrícula atualizada do Cartório de Registro de Imóveis. "
            "Documento que comprova titularidade, histórico de transmissões, ônus e ações ajuizadas."
        ),
        "price": Decimal("149.90"),
        "original_price": None,
        "delivery_days": 5,
        "is_featured": False,
        "is_system_service": True,
        "has_fixed_price": False,
        "order": 4,
        "meta_title": "Certidão de Matrícula Atualizada Online — E-Registro Brasil",
        "meta_description": "Certidão de matrícula atualizada do Registro de Imóveis online. Rápido e seguro.",
    },
    {
        "name": "Certidão de Ônus Reais",
        "slug": "certidao-de-onus-reais",
        "short_description": "Certidão de inteiro teor com todos os ônus e gravames do imóvel.",
        "description": (
            "Certidão que lista hipotecas, penhoras, alienações fiduciárias e demais gravames "
            "incidentes sobre o imóvel. Indispensável em financiamentos e transações imobiliárias."
        ),
        "price": Decimal("149.90"),
        "original_price": None,
        "delivery_days": 5,
        "is_featured": False,
        "is_system_service": True,
        "has_fixed_price": False,
        "order": 5,
        "meta_title": "Certidão de Ônus Reais Online — E-Registro Brasil",
        "meta_description": "Certidão de ônus reais do Registro de Imóveis online. Todos os gravames e hipotecas.",
    },
    {
        "name": "Certidão Negativa de Alienação Fiduciária",
        "slug": "certidao-negativa-de-alienacao-fiduciaria",
        "short_description": "Certidão que comprova inexistência de alienação fiduciária em nome do requerente.",
        "description": (
            "Certidão negativa que atesta a inexistência de alienação fiduciária de bens imóveis "
            "registrada em nome de pessoa física ou jurídica no Cartório de Registro de Imóveis."
        ),
        "price": Decimal("149.90"),
        "original_price": None,
        "delivery_days": 5,
        "is_featured": False,
        "is_system_service": True,
        "has_fixed_price": False,
        "order": 6,
        "meta_title": "Certidão Negativa de Alienação Fiduciária Online — E-Registro Brasil",
        "meta_description": "Certidão negativa de alienação fiduciária do Registro de Imóveis online.",
    },
    {
        "name": "Pesquisa de Bens",
        "slug": "pesquisa-de-bens",
        "short_description": "Pesquisa de bens imóveis registrados em nome de pessoa física ou jurídica.",
        "description": (
            "Pesquisa ampla de bens imóveis registrados em nome de uma pessoa junto ao Cartório de "
            "Registro de Imóveis. Utilizada em processos judiciais, planejamento patrimonial e "
            "due diligence."
        ),
        "price": Decimal("149.90"),
        "original_price": None,
        "delivery_days": 5,
        "is_featured": False,
        "is_system_service": True,
        "has_fixed_price": False,
        "order": 7,
        "meta_title": "Pesquisa de Bens Imóveis Online — E-Registro Brasil",
        "meta_description": "Pesquisa de bens imóveis registrados em nome de pessoa no Registro de Imóveis.",
    },
]


def seed_imoveis(apps, schema_editor):
    """
    Cria (ou garante) a categoria Imóveis e todos os seus serviços.
    Totalmente idempotente — usa get_or_create por slug.
    Serviços já existentes NÃO são sobrescritos (preserva preços customizados).
    Apenas is_system_service=True é retroativamente marcado em registros existentes.
    """
    Category = apps.get_model("products", "Category")
    Product = apps.get_model("products", "Product")

    # ── Garante que a categoria existe ───────────────────────────────────────
    categoria, _ = Category.objects.get_or_create(
        slug=_CATEGORIA["slug"],
        defaults={
            "name": _CATEGORIA["name"],
            "order": _CATEGORIA["order"],
            "icon_svg": _CATEGORIA["icon_svg"],
            "is_active": True,
            "description": "",
        },
    )

    # ── Garante que cada serviço existe ──────────────────────────────────────
    slugs_processados = []
    for svc in _SERVICOS:
        produto, criado = Product.objects.get_or_create(
            slug=svc["slug"],
            defaults={
                "name": svc["name"],
                "category": categoria,
                "short_description": svc["short_description"],
                "description": svc["description"],
                "price": svc["price"],
                "original_price": svc["original_price"],
                "delivery_days": svc["delivery_days"],
                "is_active": True,
                "is_featured": svc["is_featured"],
                "is_system_service": True,
                "has_fixed_price": svc["has_fixed_price"],
                "order": svc["order"],
                "meta_title": svc["meta_title"],
                "meta_description": svc["meta_description"],
                "icon_svg": "",
                "tipo_cartorio": "imoveis",
            },
        )
        slugs_processados.append(svc["slug"])

        # Se já existia, apenas garante is_system_service e category corretos
        if not criado:
            campos_atualizados = []
            if not produto.is_system_service:
                produto.is_system_service = True
                campos_atualizados.append("is_system_service")
            if produto.category_id != categoria.pk:
                produto.category = categoria
                campos_atualizados.append("category")
            if campos_atualizados:
                produto.save(update_fields=campos_atualizados)

    # ── Marca retroativamente qualquer produto de imóveis já existente ───────
    Product.objects.filter(
        slug__in=slugs_processados,
        is_system_service=False,
    ).update(is_system_service=True)


def noop(apps, schema_editor):
    """Reverse não-destrutivo: não remove dados de produção."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0021_alter_product_has_fixed_price"),
    ]

    operations = [
        migrations.RunPython(seed_imoveis, noop),
    ]
