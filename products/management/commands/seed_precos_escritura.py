"""
Popula os preços por estado para Certidão de Escritura.

Uso:
    python manage.py seed_precos_escritura
    python manage.py seed_precos_escritura --reset   # reescreve todos os preços
    python manage.py seed_precos_escritura --slug=outro-slug
"""
from django.core.management.base import BaseCommand, CommandError

from products.models import Product, State, ServiceStatePrice
from products.services import PRECOS_CERTIDAO_ESCRITURA

SLUG_ESCRITURA = "certidao-de-escritura"


class Command(BaseCommand):
    help = "Popula preços por estado para Certidão de Escritura"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Atualiza preços existentes (sobrescreve valores já gravados)",
        )
        parser.add_argument(
            "--slug",
            default=SLUG_ESCRITURA,
            help=f"Slug do produto (padrão: {SLUG_ESCRITURA})",
        )

    def handle(self, *args, **options):
        slug = options["slug"]
        reset = options["reset"]

        # 1. Garante que os estados existem no banco
        self._seed_states()

        # 2. Busca o produto
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            raise CommandError(
                f"Produto com slug '{slug}' não encontrado.\n"
                "Verifique o slug ou use --slug=<slug-correto>."
            )

        self.stdout.write(f"Produto: {product.name} (preço base: R$ {product.price})")

        # 3. Popula preços
        criados = 0
        atualizados = 0

        for code, preco in PRECOS_CERTIDAO_ESCRITURA.items():
            try:
                state = State.objects.get(code=code)
            except State.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  Estado {code} não encontrado — pulando"))
                continue

            ssp, created = ServiceStatePrice.objects.get_or_create(
                service=product,
                state=state,
                defaults={"price": preco, "is_active": True},
            )
            if created:
                criados += 1
                self.stdout.write(f"  + {code}: R$ {preco}")
            elif reset:
                ssp.price = preco
                ssp.is_active = True
                ssp.save(update_fields=["price", "is_active"])
                atualizados += 1
                self.stdout.write(f"  ~ {code}: R$ {preco} (atualizado)")

        # 4. Resumo
        total = ServiceStatePrice.objects.filter(service=product, is_active=True).count()
        self.stdout.write(self.style.SUCCESS(
            f"\nConcluído: {criados} criado(s), {atualizados} atualizado(s). "
            f"Total ativo: {total} estado(s)."
        ))

    def _seed_states(self):
        from products.models import ESTADOS_BR
        for code, name in ESTADOS_BR:
            State.objects.get_or_create(code=code, defaults={"name": name})
