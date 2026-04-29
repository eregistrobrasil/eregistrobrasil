from django.core.management.base import BaseCommand
from products.models import Product


FEATURED_PRODUCTS = [
    "Certidão de Nascimento 2ª Via",
    "Certidão de Casamento 2ª Via",
    "Certidão de Imóvel",
    "Pacote de Certidões / Compra e Venda de Imóvel",
    "Certidão de Testamento",
    "Certidão de Óbito 2ª Via",
]


class Command(BaseCommand):
    help = "Define exatamente quais produtos aparecem em destaque na home"

    def handle(self, *args, **kwargs):
        # 1. Remove destaque de todos
        total_cleared = Product.objects.update(is_featured=False)
        self.stdout.write(f"Destaque removido de {total_cleared} produto(s).")

        # 2. Marca apenas os desejados, na ordem correta
        not_found = []
        for order, name in enumerate(FEATURED_PRODUCTS, start=1):
            updated = Product.objects.filter(name__iexact=name).update(
                is_featured=True, order=order
            )
            if updated:
                self.stdout.write(self.style.SUCCESS(f"  [{order}] {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"  [não encontrado] {name}"))
                not_found.append(name)

        if not_found:
            self.stdout.write(
                self.style.WARNING(f"\nAtenção: {len(not_found)} produto(s) não encontrado(s).")
            )
        self.stdout.write(self.style.SUCCESS("Destaques configurados com sucesso!"))
