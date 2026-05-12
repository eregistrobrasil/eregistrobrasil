"""
Seed de preços por estado para as 10 variantes de Escritura.
Todos os serviços usam a mesma tabela de preços de PRECOS_CERTIDAO_ESCRITURA.
"""
from django.core.management.base import BaseCommand
from products.models import Product, State, ServiceStatePrice
from products.services import PRECOS_CERTIDAO_ESCRITURA


SLUGS_ESCRITURA_VARIANTES = [
    'certidao-de-escritura-de-ata-notarial',
    'certidao-de-escritura-de-compra-e-venda',
    'certidao-de-escritura-de-divorcio',
    'certidao-de-escritura-de-doacao',
    'certidao-de-escritura-de-emancipacao',
    'certidao-de-escritura-de-hipoteca',
    'certidao-de-escritura-de-inventario',
    'certidao-de-escritura-de-pacto-antenupcial',
    'certidao-de-escritura-de-permuta',
    'certidao-de-escritura-de-testamento',
]


class Command(BaseCommand):
    help = 'Seed preços por estado para os 10 serviços de variantes de Escritura'

    def handle(self, *args, **options):
        total_criados = 0
        total_atualizados = 0

        for slug in SLUGS_ESCRITURA_VARIANTES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Produto não encontrado: {slug} — pulando'))
                continue

            for uf, preco in PRECOS_CERTIDAO_ESCRITURA.items():
                try:
                    state = State.objects.get(code=uf)
                except State.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Estado não encontrado: {uf}'))
                    continue

                obj, created = ServiceStatePrice.objects.update_or_create(
                    service=product,
                    state=state,
                    defaults={'price': preco, 'is_active': True},
                )
                if created:
                    total_criados += 1
                else:
                    total_atualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Concluído: {total_criados} criados, {total_atualizados} atualizados '
            f'em {len(SLUGS_ESCRITURA_VARIANTES)} produtos.'
        ))
