from decimal import Decimal
from django.db import migrations


def setup_certidao_negativa_testamento(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Product = apps.get_model('products', 'Product')

    # Desativar serviços legados que não possuem páginas dedicadas
    Product.objects.filter(
        slug__in=['escritura-publica', 'procuracao-publica']
    ).update(is_active=False)

    # Garantir que a categoria "Busca" existe
    busca_cat, _ = Category.objects.get_or_create(
        slug='busca',
        defaults={
            'name': 'Busca',
            'order': 7,
            'is_active': True,
        },
    )

    # Criar ou reativar o produto "Certidão Negativa de Testamento"
    product, created = Product.objects.get_or_create(
        slug='certidao-negativa-de-testamento',
        defaults={
            'name': 'Certidão Negativa de Testamento',
            'category': busca_cat,
            'description': (
                'Pesquisa nacional de testamentos para verificar a existência de testamento '
                'registrado em nome do falecido. A busca é realizada em Tabelionatos de Notas '
                'de todo o Brasil pelo CPF, nome e dados do falecido informados.'
            ),
            'short_description': (
                'Pesquisa nacional de testamentos registrados em nome do falecido '
                'em tabelionatos de todo o Brasil.'
            ),
            'price': Decimal('239.90'),
            'delivery_days': 15,
            'is_active': True,
            'is_system_service': True,
            'has_fixed_price': True,
            'meta_title': 'Certidão Negativa de Testamento Online — E-Registro Brasil',
            'meta_description': (
                'Solicite a pesquisa de testamentos em nome do falecido. '
                'Busca nacional em tabelionatos de notas de todo o Brasil.'
            ),
        },
    )
    if not created:
        product.is_active = True
        product.price = Decimal('239.90')
        product.category = busca_cat
        product.has_fixed_price = True
        if not product.name or product.name == 'Certidão Negativa de Testamento':
            product.name = 'Certidão Negativa de Testamento'
        product.save()


def reverse_setup(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(slug='certidao-negativa-de-testamento').update(is_active=False)


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0025_deactivate_certidao_negativa_testamento'),
    ]

    operations = [
        migrations.RunPython(
            setup_certidao_negativa_testamento,
            reverse_code=reverse_setup,
        ),
    ]
