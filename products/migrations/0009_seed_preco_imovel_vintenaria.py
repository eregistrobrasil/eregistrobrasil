"""
Data migration: seed dos preços de Vintenária por estado.
Chave interna: 'vintenaria', conforme definido em TIPOS_CERTIDAO_IMOVEL.
Idempotente: get_or_create + atualiza se divergir.
"""
from decimal import Decimal
from django.db import migrations


PRECOS_VINTENARIA = [
    ('AC', Decimal('289.90')),
    ('AL', Decimal('169.90')),
    ('AP', Decimal('219.90')),
    ('AM', Decimal('239.90')),
    ('BA', Decimal('274.89')),
    ('CE', Decimal('199.90')),
    ('ES', Decimal('229.95')),
    ('DF', Decimal('122.88')),
    ('GO', Decimal('249.90')),
    ('MA', Decimal('219.90')),
    ('MT', Decimal('149.90')),
    ('MS', Decimal('229.90')),
    ('MG', Decimal('229.90')),
    ('PA', Decimal('289.90')),
    ('PB', Decimal('285.95')),
    ('PR', Decimal('229.90')),
    ('PE', Decimal('169.90')),
    ('PI', Decimal('189.90')),
    ('RJ', Decimal('349.90')),
    ('RN', Decimal('379.90')),
    ('RS', Decimal('269.90')),
    ('RO', Decimal('139.90')),
    ('RR', Decimal('119.90')),
    ('SC', Decimal('189.90')),
    ('SP', Decimal('229.95')),
    ('SE', Decimal('149.90')),
    ('TO', Decimal('149.90')),
]


def seed_vintenaria(apps, schema_editor):
    State = apps.get_model('products', 'State')
    PrecoImovelEstado = apps.get_model('products', 'PrecoImovelEstado')

    for uf, price in PRECOS_VINTENARIA:
        state = State.objects.filter(code=uf).first()
        if not state:
            continue
        obj, created = PrecoImovelEstado.objects.get_or_create(
            tipo_certidao='vintenaria',
            state=state,
            defaults={'price': price, 'is_active': True},
        )
        if not created and obj.price != price:
            obj.price = price
            obj.save(update_fields=['price'])


def unseed_vintenaria(apps, schema_editor):
    PrecoImovelEstado = apps.get_model('products', 'PrecoImovelEstado')
    PrecoImovelEstado.objects.filter(tipo_certidao='vintenaria').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_seed_preco_imovel_inteiro_teor'),
    ]

    operations = [
        migrations.RunPython(seed_vintenaria, reverse_code=unseed_vintenaria),
    ]
