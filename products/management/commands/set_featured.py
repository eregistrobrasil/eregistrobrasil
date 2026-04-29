from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Product
from decimal import Decimal


FEATURED_NAMES = [
    "Certidão de Nascimento 2ª Via",
    "Certidão de Casamento 2ª Via",
    "Certidão de Óbito 2ª Via",
]

NEW_PRODUCTS = [
    {
        "category_slug": "imoveis",
        "name": "Certidão de Imóvel",
        "price": "149.90",
        "original_price": "199.90",
        "days": 5,
        "short": "Certidão completa do imóvel com histórico de proprietários, ônus e ações reais.",
        "featured": True,
    },
    {
        "category_slug": "imoveis",
        "name": "Pacote de Certidões / Compra e Venda de Imóvel",
        "price": "399.90",
        "original_price": "599.90",
        "days": 7,
        "short": (
            "Pacote completo de certidões necessárias para compra e venda de imóvel: "
            "matrícula atualizada, ônus reais, certidões pessoais do vendedor e negativas de débitos."
        ),
        "featured": True,
    },
    {
        "category_slug": "notas",
        "name": "Certidão de Testamento",
        "price": "129.90",
        "original_price": "169.90",
        "days": 7,
        "short": "Pesquisa e certidão de testamentos registrados em cartório de notas em todo o território nacional.",
        "featured": True,
    },
]


class Command(BaseCommand):
    help = "Marca produtos como destaque e cria novos produtos se necessário"

    def handle(self, *args, **kwargs):
        # Marcar produtos existentes como destaque
        for name in FEATURED_NAMES:
            updated = Product.objects.filter(name=name).update(is_featured=True)
            if updated:
                self.stdout.write(self.style.SUCCESS(f"Marcado como destaque: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Produto não encontrado: {name}"))

        # Criar novos produtos se não existirem e marcá-los como destaque
        for prod_data in NEW_PRODUCTS:
            category = Category.objects.filter(slug=prod_data["category_slug"]).first()
            if not category:
                # Tenta encontrar por nome parcial
                category = Category.objects.filter(
                    name__icontains=prod_data["category_slug"]
                ).first()
            if not category:
                self.stdout.write(
                    self.style.WARNING(
                        f"Categoria '{prod_data['category_slug']}' não encontrada. "
                        f"Produto '{prod_data['name']}' não foi criado."
                    )
                )
                continue

            product, created = Product.objects.get_or_create(
                name=prod_data["name"],
                defaults={
                    "slug": slugify(prod_data["name"]),
                    "category": category,
                    "description": prod_data["short"],
                    "short_description": prod_data["short"],
                    "price": Decimal(prod_data["price"]),
                    "original_price": Decimal(prod_data["original_price"]) if prod_data.get("original_price") else None,
                    "delivery_days": prod_data["days"],
                    "is_active": True,
                    "is_featured": prod_data.get("featured", False),
                    "order": 0,
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Criado e marcado como destaque: {prod_data['name']}"))
            else:
                product.is_featured = prod_data.get("featured", False)
                product.save(update_fields=["is_featured"])
                self.stdout.write(self.style.SUCCESS(f"Atualizado como destaque: {prod_data['name']}"))

        self.stdout.write(self.style.SUCCESS("Concluído!"))
