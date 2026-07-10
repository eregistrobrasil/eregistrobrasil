from decimal import Decimal
from django.db import migrations

PRECO_NOVO = Decimal('237.90')
PRECO_ANTIGO = Decimal('239.90')


def atualizar_preco(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(slug='certidao-negativa-de-testamento').update(price=PRECO_NOVO)


def reverter_preco(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(slug='certidao-negativa-de-testamento').update(price=PRECO_ANTIGO)


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0028_seed_imagem_static'),
    ]

    operations = [
        migrations.RunPython(atualizar_preco, reverse_code=reverter_preco),
    ]
