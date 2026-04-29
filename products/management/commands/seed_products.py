from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Product
from decimal import Decimal


SEED_DATA = [
    {
        "name": "Registro Civil",
        "icon_svg": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>',
        "order": 1,
        "products": [
            {"name": "Certidão de Nascimento 2ª Via", "price": "89.90", "original_price": "129.90", "days": 7,
             "short": "Certidão de nascimento atualizada para uso em processos, casamentos e outros fins legais."},
            {"name": "Certidão de Casamento 2ª Via", "price": "89.90", "original_price": "129.90", "days": 7,
             "short": "Segunda via da certidão de casamento com validade em todo território nacional."},
            {"name": "Certidão de Óbito 2ª Via", "price": "89.90", "original_price": "129.90", "days": 7,
             "short": "Certidão de óbito para fins de inventário, pensão ou outros processos legais."},
        ],
    },
    {
        "name": "Imóveis",
        "icon_svg": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>',
        "order": 2,
        "products": [
            {"name": "Certidão de Matrícula Atualizada", "price": "149.90", "original_price": "199.90", "days": 5,
             "short": "Certidão de matrícula do imóvel atualizada com histórico de proprietários e ônus."},
            {"name": "Certidão de Ônus Reais", "price": "149.90", "original_price": "199.90", "days": 5,
             "short": "Certidão de ônus e ações reais sobre o imóvel para transações imobiliárias."},
            {"name": "Certidão Negativa de Alienação Fiduciária", "price": "129.90", "original_price": "169.90", "days": 7,
             "short": "Certifica a inexistência de alienação fiduciária sobre o imóvel."},
        ],
    },
    {
        "name": "Notas",
        "icon_svg": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>',
        "order": 3,
        "products": [
            {"name": "Procuração Pública", "price": "199.90", "original_price": None, "days": 3,
             "short": "Lavratura de procuração pública em cartório de notas com poderes definidos."},
            {"name": "Escritura Pública", "price": "299.90", "original_price": None, "days": 5,
             "short": "Elaboração e lavratura de escritura pública para transferência de bens e outros fins."},
        ],
    },
    {
        "name": "Protesto",
        "icon_svg": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>',
        "order": 4,
        "products": [
            {"name": "Certidão de Protesto", "price": "79.90", "original_price": "99.90", "days": 3,
             "short": "Certidão de protesto de títulos para pessoa física ou jurídica em qualquer praça."},
            {"name": "Pesquisa de Protesto Nacional", "price": "59.90", "original_price": "79.90", "days": 2,
             "short": "Pesquisa de protestos em nível nacional via sistema CRA."},
        ],
    },
    {
        "name": "Federais e Estaduais",
        "icon_svg": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>',
        "order": 5,
        "products": [
            {"name": "CND Federal (Receita Federal)", "price": "49.90", "original_price": "69.90", "days": 1,
             "short": "Certidão Negativa de Débitos federais junto à Receita Federal."},
            {"name": "Certidão FGTS/INSS", "price": "49.90", "original_price": "69.90", "days": 1,
             "short": "Certidão de regularidade do FGTS para pessoa física ou jurídica."},
            {"name": "CND Estadual (SEFAZ)", "price": "49.90", "original_price": "69.90", "days": 1,
             "short": "Certidão Negativa de Débitos estaduais para fins de licitação, contratos e outros."},
        ],
    },
    {
        "name": "Pesquisa",
        "icon_svg": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>',
        "order": 6,
        "products": [
            {"name": "Busca em Cartórios", "price": "89.90", "original_price": None, "days": 5,
             "short": "Pesquisa ampla em cartórios de registro civil para localização de documentos."},
        ],
    },
    {
        "name": "Tradução e Apostilamento",
        "icon_svg": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"/></svg>',
        "order": 7,
        "products": [
            {"name": "Tradução Juramentada", "price": "350.00", "original_price": None, "days": 10,
             "short": "Tradução juramentada de documentos por tradutor público juramentado registrado na Junta Comercial."},
            {"name": "Apostila de Haia", "price": "199.90", "original_price": "249.90", "days": 7,
             "short": "Apostilamento de documentos para reconhecimento em países signatários da Convenção de Haia."},
        ],
    },
]


class Command(BaseCommand):
    help = "Seed de categorias e produtos iniciais"

    def handle(self, *args, **kwargs):
        if Product.objects.exists():
            self.stdout.write(self.style.WARNING("Produtos já existem. Seed ignorado."))
            return

        for cat_data in SEED_DATA:
            category, _ = Category.objects.get_or_create(
                slug=slugify(cat_data["name"]),
                defaults={
                    "name": cat_data["name"],
                    "icon_svg": cat_data["icon_svg"],
                    "order": cat_data["order"],
                    "is_active": True,
                },
            )

            for prod_data in cat_data["products"]:
                slug = slugify(prod_data["name"])
                # Garantir slug único
                base_slug = slug
                counter = 1
                while Product.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                Product.objects.create(
                    name=prod_data["name"],
                    slug=slug,
                    category=category,
                    short_description=prod_data["short"],
                    description=prod_data["short"],
                    price=Decimal(prod_data["price"]),
                    original_price=Decimal(prod_data["original_price"]) if prod_data["original_price"] else None,
                    delivery_days=prod_data["days"],
                    is_active=True,
                    is_featured=True,
                )
                self.stdout.write(f"  + {prod_data['name']}")

            self.stdout.write(self.style.SUCCESS(f"Categoria: {cat_data['name']}"))

        self.stdout.write(self.style.SUCCESS("Seed concluído!"))
