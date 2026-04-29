from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Product
from decimal import Decimal


MISSING_DATA = [
    # ─────────────────────────────────────────────
    # REGISTRO CIVIL
    # ─────────────────────────────────────────────
    {
        "category": "Registro Civil",
        "name": "Certidão de Procuração",
        "price": "89.90", "original_price": "129.90", "days": 7,
        "short": "Certidão de procuração lavrada em cartório de registro civil para representação legal.",
    },
    {
        "category": "Registro Civil",
        "name": "Certidão de Interdição",
        "price": "99.90", "original_price": "149.90", "days": 10,
        "short": "Certidão de interdição civil para processos de curatela, tutela e fins legais.",
    },
    {
        "category": "Registro Civil",
        "name": "Monitoramento de CPF/CNPJ",
        "price": "49.90", "original_price": "69.90", "days": 1,
        "short": "Monitoramento contínuo de CPF ou CNPJ para identificar registros, protestos e pendências.",
    },

    # ─────────────────────────────────────────────
    # IMÓVEIS
    # ─────────────────────────────────────────────
    {
        "category": "Imóveis",
        "name": "Certidão de Penhor de Safra",
        "price": "149.90", "original_price": "199.90", "days": 5,
        "short": "Certidão de penhor de safra registrado em cartório para fins de financiamento agropecuário.",
    },
    {
        "category": "Imóveis",
        "name": "Pesquisa de Bens",
        "price": "99.90", "original_price": "139.90", "days": 5,
        "short": "Pesquisa de bens imóveis e móveis registrados em nome de pessoa física ou jurídica.",
    },
    {
        "category": "Imóveis",
        "name": "Monitoramento de CPF/CNPJ - Imóveis",
        "price": "49.90", "original_price": "69.90", "days": 1,
        "short": "Monitoramento de registros de imóveis vinculados a CPF ou CNPJ.",
    },

    # ─────────────────────────────────────────────
    # NOTAS
    # ─────────────────────────────────────────────
    {
        "category": "Notas",
        "name": "Certidão de Procuração",
        "price": "129.90", "original_price": "179.90", "days": 5,
        "short": "Certidão de procuração pública lavrada em cartório de notas com poderes específicos ou gerais.",
    },
    {
        "category": "Notas",
        "name": "Certidão de Escritura",
        "price": "149.90", "original_price": "199.90", "days": 5,
        "short": "Certidão de escritura pública registrada em cartório de notas.",
    },
    {
        "category": "Notas",
        "name": "Certidão de Escritura de União Estável",
        "price": "149.90", "original_price": "199.90", "days": 5,
        "short": "Certidão de escritura pública de reconhecimento ou dissolução de união estável.",
    },
    {
        "category": "Notas",
        "name": "Certidão de Escritura de Pacto Antenupcial",
        "price": "149.90", "original_price": "199.90", "days": 5,
        "short": "Certidão de pacto antenupcial registrado em cartório de notas para fins matrimoniais.",
    },
    {
        "category": "Notas",
        "name": "Certidão de Escritura de Compra e Venda",
        "price": "149.90", "original_price": "199.90", "days": 5,
        "short": "Certidão de escritura pública de compra e venda de bens imóveis ou móveis.",
    },
    {
        "category": "Notas",
        "name": "Certidão de Escritura de Doação",
        "price": "149.90", "original_price": "199.90", "days": 5,
        "short": "Certidão de escritura pública de doação registrada em cartório de notas.",
    },
    {
        "category": "Notas",
        "name": "Certidão de Escritura de Permuta",
        "price": "149.90", "original_price": "199.90", "days": 5,
        "short": "Certidão de escritura de permuta (troca) de bens registrada em cartório de notas.",
    },
    {
        "category": "Notas",
        "name": "Certidão de Escritura de Hipoteca",
        "price": "149.90", "original_price": "199.90", "days": 5,
        "short": "Certidão de escritura de hipoteca registrada em cartório de notas.",
    },
    {
        "category": "Notas",
        "name": "Certidão de Escritura de Inventário",
        "price": "199.90", "original_price": "269.90", "days": 7,
        "short": "Certidão de escritura pública de inventário e partilha de bens registrada em cartório.",
    },
    {
        "category": "Notas",
        "name": "Certidão de Escritura de Testamento",
        "price": "149.90", "original_price": "199.90", "days": 7,
        "short": "Certidão de testamento público ou cerrado registrado em cartório de notas.",
    },
    {
        "category": "Notas",
        "name": "Certidão de Escritura de Emancipação",
        "price": "129.90", "original_price": "169.90", "days": 5,
        "short": "Certidão de escritura pública de emancipação de menor registrada em cartório.",
    },
    {
        "category": "Notas",
        "name": "Certidão de Escritura de Divórcio",
        "price": "149.90", "original_price": "199.90", "days": 5,
        "short": "Certidão de escritura pública de divórcio consensual registrada em cartório de notas.",
    },
    {
        "category": "Notas",
        "name": "Certidão de Escritura de Ata Notarial",
        "price": "149.90", "original_price": "199.90", "days": 5,
        "short": "Certidão de ata notarial registrada em cartório de notas para fins probatórios.",
    },

    # ─────────────────────────────────────────────
    # FEDERAIS E ESTADUAIS
    # ─────────────────────────────────────────────
    {
        "category": "Federais e Estaduais",
        "name": "Certidão de Antecedentes Criminais",
        "price": "49.90", "original_price": "69.90", "days": 2,
        "short": "Certidão de antecedentes criminais emitida por órgão federal ou estadual.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "TSE - Certidão de Quitação Eleitoral",
        "price": "29.90", "original_price": "49.90", "days": 1,
        "short": "Certidão de quitação eleitoral emitida pelo Tribunal Superior Eleitoral (TSE).",
    },
    {
        "category": "Federais e Estaduais",
        "name": "Certidão Negativa de Débitos Trabalhistas",
        "price": "49.90", "original_price": "69.90", "days": 1,
        "short": "Certidão Negativa de Débitos Trabalhistas (CNDT) para pessoa física ou jurídica.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "Certidão Negativa de Ações Criminais",
        "price": "49.90", "original_price": "69.90", "days": 2,
        "short": "Certidão negativa de distribuição de ações criminais em âmbito federal ou estadual.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "MPF - Certidão Negativa",
        "price": "49.90", "original_price": "69.90", "days": 2,
        "short": "Certidão negativa emitida pelo Ministério Público Federal (MPF).",
    },
    {
        "category": "Federais e Estaduais",
        "name": "Certidão de Distribuição da Justiça Federal",
        "price": "59.90", "original_price": "79.90", "days": 2,
        "short": "Certidão de distribuição de ações na Justiça Federal em qualquer seção judiciária.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "Certidão de Propriedade de Aeronave",
        "price": "79.90", "original_price": "109.90", "days": 3,
        "short": "Certidão de propriedade de aeronave emitida pela ANAC ou RAB.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "Certidão IBAMA - Certidão de Embargos",
        "price": "49.90", "original_price": "69.90", "days": 2,
        "short": "Certidão de embargos e infrações ambientais emitida pelo IBAMA.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "Certidão Negativa de Débitos do IBAMA",
        "price": "49.90", "original_price": "69.90", "days": 2,
        "short": "Certidão negativa de débitos junto ao IBAMA para pessoa física ou jurídica.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "CNJ - Improbidade Administrativa e Inelegibilidade",
        "price": "49.90", "original_price": "69.90", "days": 1,
        "short": "Certidão do Banco Nacional de Condenações por Improbidade Administrativa emitida pelo CNJ.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "Certidão de Cumprimento da Cota Legal de PCDs",
        "price": "49.90", "original_price": "69.90", "days": 2,
        "short": "Certidão de cumprimento da cota obrigatória de Pessoas com Deficiência (PCDs) junto ao MTE.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "MT - Certidão de Débitos",
        "price": "49.90", "original_price": "69.90", "days": 2,
        "short": "Certidão de débitos junto ao Ministério do Trabalho (MT).",
    },
    {
        "category": "Federais e Estaduais",
        "name": "MT - Certidão de Infrações Trabalhistas",
        "price": "49.90", "original_price": "69.90", "days": 2,
        "short": "Certidão de infrações trabalhistas registradas junto ao Ministério do Trabalho (MT).",
    },
    {
        "category": "Federais e Estaduais",
        "name": "Cadastro de Imóveis Rurais - CAFIR",
        "price": "59.90", "original_price": "79.90", "days": 2,
        "short": "Certidão do Cadastro de Imóveis Rurais (CAFIR) emitida pela Receita Federal.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "CND ITR - Receita Federal",
        "price": "49.90", "original_price": "69.90", "days": 1,
        "short": "Certidão Negativa de Débitos de ITR (Imposto Territorial Rural) emitida pela Receita Federal.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "STF - Certidão Distribuidor",
        "price": "59.90", "original_price": "79.90", "days": 2,
        "short": "Certidão de distribuição de processos no Supremo Tribunal Federal (STF).",
    },
    {
        "category": "Federais e Estaduais",
        "name": "STJ - Certidão do STJ",
        "price": "59.90", "original_price": "79.90", "days": 2,
        "short": "Certidão de distribuição de processos no Superior Tribunal de Justiça (STJ).",
    },
    {
        "category": "Federais e Estaduais",
        "name": "TCU - Certidão de Tribunal de Contas",
        "price": "59.90", "original_price": "79.90", "days": 2,
        "short": "Certidão emitida pelo Tribunal de Contas da União (TCU) para fins de licitação e contratos.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "Certidão de Distribuição Estadual (Cível, Criminal, Falência)",
        "price": "59.90", "original_price": "79.90", "days": 3,
        "short": "Certidão de distribuição de ações cíveis, criminais e falimentares no âmbito estadual.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "Certidão Negativa de Débitos Ambientais",
        "price": "49.90", "original_price": "69.90", "days": 2,
        "short": "Certidão negativa de débitos e autuações ambientais perante órgãos estaduais ou federais.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "Junta Comercial - Certidão da Empresa",
        "price": "79.90", "original_price": "109.90", "days": 3,
        "short": "Certidão simplificada ou inteiro teor da empresa emitida pela Junta Comercial Estadual.",
    },
    {
        "category": "Federais e Estaduais",
        "name": "MPE - Certidão de Inquérito Civil",
        "price": "59.90", "original_price": "79.90", "days": 3,
        "short": "Certidão de inquérito civil emitida pelo Ministério Público Estadual (MPE).",
    },
    {
        "category": "Federais e Estaduais",
        "name": "MPE - Certidão de Inquérito Criminal",
        "price": "59.90", "original_price": "79.90", "days": 3,
        "short": "Certidão de inquérito criminal emitida pelo Ministério Público Estadual (MPE).",
    },
    {
        "category": "Federais e Estaduais",
        "name": "Certidão de Tributos da Procuradoria Geral do Estado",
        "price": "49.90", "original_price": "69.90", "days": 2,
        "short": "Certidão de débitos tributários estaduais emitida pela Procuradoria Geral do Estado (PGE).",
    },
    {
        "category": "Federais e Estaduais",
        "name": "TRT - Certidão de Ações Trabalhistas (CEAT)",
        "price": "59.90", "original_price": "79.90", "days": 2,
        "short": "Certidão de Ações Trabalhistas (CEAT) emitida pelo Tribunal Regional do Trabalho (TRT).",
    },
]


MAX_SLUG = 50


def _unique_slug(base_slug):
    # Truncate to leave room for potential "-N" suffix
    base_slug = base_slug[:MAX_SLUG]
    slug = base_slug
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        suffix = f"-{counter}"
        slug = base_slug[: MAX_SLUG - len(suffix)] + suffix
        counter += 1
    return slug


class Command(BaseCommand):
    help = "Adiciona certidões que ainda não existem no banco de dados"

    def handle(self, *args, **kwargs):
        created_count = 0
        skipped_count = 0

        for item in MISSING_DATA:
            # Busca a categoria pelo nome (case-insensitive)
            category = Category.objects.filter(name__iexact=item["category"]).first()
            if not category:
                # Tenta por slug
                category = Category.objects.filter(
                    slug=slugify(item["category"])
                ).first()
            if not category:
                self.stdout.write(
                    self.style.WARNING(
                        f"[CATEGORIA NÃO ENCONTRADA] '{item['category']}' — pulando '{item['name']}'"
                    )
                )
                skipped_count += 1
                continue

            # Verifica se já existe pelo nome (case-insensitive, na mesma categoria)
            if Product.objects.filter(
                name__iexact=item["name"], category=category
            ).exists():
                self.stdout.write(f"  [já existe] {item['name']}")
                skipped_count += 1
                continue

            slug = _unique_slug(slugify(item["name"]))
            Product.objects.create(
                name=item["name"],
                slug=slug,
                category=category,
                description=item["short"],
                short_description=item["short"],
                price=Decimal(item["price"]),
                original_price=Decimal(item["original_price"]) if item.get("original_price") else None,
                delivery_days=item["days"],
                is_active=True,
                is_featured=False,
                order=0,
            )
            self.stdout.write(
                self.style.SUCCESS(f"  [criado] {item['name']} ({item['category']})")
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nConcluído! {created_count} produto(s) criado(s), {skipped_count} ignorado(s)."
            )
        )
