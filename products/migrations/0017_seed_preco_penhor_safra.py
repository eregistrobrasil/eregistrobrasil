"""
Data migration: seed dos preços de Penhor de Safra por estado.
Chave interna: 'penhor_safra'.
Idempotente: get_or_create + atualiza se divergir.
"""
from decimal import Decimal
from django.db import migrations


PRECOS_PENHOR_SAFRA = [
    ('AC', Decimal('139.90')),
    ('AL', Decimal('187.90')),
    ('AP', Decimal('159.90')),
    ('AM', Decimal('209.90')),
    ('BA', Decimal('259.90')),
    ('CE', Decimal('279.90')),
    ('ES', Decimal('245.90')),
    ('DF', Decimal('119.90')),
    ('GO', Decimal('218.90')),
    ('MA', Decimal('229.90')),
    ('MT', Decimal('167.90')),
    ('MS', Decimal('167.90')),
    ('MG', Decimal('229.90')),
    ('PA', Decimal('149.90')),
    ('PB', Decimal('179.90')),
    ('PR', Decimal('229.90')),
    ('PE', Decimal('214.90')),
    ('PI', Decimal('195.90')),
    ('RJ', Decimal('195.90')),
    ('RN', Decimal('699.90')),
    ('RS', Decimal('169.90')),
    ('RO', Decimal('239.90')),
    ('RR', Decimal('229.90')),
    ('SC', Decimal('189.90')),
    ('SP', Decimal('219.90')),
    ('SE', Decimal('149.90')),
    ('TO', Decimal('189.90')),
]


def seed_penhor_safra(apps, schema_editor):
    State = apps.get_model('products', 'State')
    PrecoImovelEstado = apps.get_model('products', 'PrecoImovelEstado')

    for uf, price in PRECOS_PENHOR_SAFRA:
        state = State.objects.filter(code=uf).first()
        if not state:
            continue
        obj, created = PrecoImovelEstado.objects.get_or_create(
            tipo_certidao='penhor_safra',
            state=state,
            defaults={'price': price, 'is_active': True},
        )
        if not created and obj.price != price:
            obj.price = price
            obj.save(update_fields=['price'])


def unseed_penhor_safra(apps, schema_editor):
    PrecoImovelEstado = apps.get_model('products', 'PrecoImovelEstado')
    PrecoImovelEstado.objects.filter(tipo_certidao='penhor_safra').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0016_seed_preco_imovel_quesitos'),
    ]

    operations = [
        migrations.RunPython(seed_penhor_safra, reverse_code=unseed_penhor_safra),
    ]
