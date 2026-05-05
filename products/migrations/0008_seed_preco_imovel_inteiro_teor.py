"""
Data migration: seed dos preços de Inteiro Teor e Ônus da Ação por estado.
A chave interna é 'inteiro_teor', conforme definido em TIPOS_CERTIDAO_IMOVEL.
Idempotente: usa get_or_create e atualiza somente se o preço divergir.
"""
from decimal import Decimal
from django.db import migrations


PRECOS_INTEIRO_TEOR = [
    ('AC', Decimal('299.90')),
    ('AL', Decimal('169.90')),
    ('AP', Decimal('299.90')),
    ('AM', Decimal('599.90')),
    ('BA', Decimal('274.89')),
    ('CE', Decimal('699.90')),
    ('ES', Decimal('229.90')),
    ('DF', Decimal('249.90')),
    ('GO', Decimal('249.90')),
    ('MA', Decimal('552.33')),
    ('MT', Decimal('399.90')),
    ('MS', Decimal('229.90')),
    ('MG', Decimal('339.90')),
    ('PA', Decimal('399.90')),
    ('PB', Decimal('349.90')),
    ('PR', Decimal('229.90')),
    ('PE', Decimal('189.90')),
    ('PI', Decimal('239.90')),
    ('RJ', Decimal('349.90')),
    ('RN', Decimal('637.67')),
    ('RS', Decimal('299.90')),
    ('RO', Decimal('219.90')),
    ('RR', Decimal('199.90')),
    ('SC', Decimal('249.90')),
    ('SP', Decimal('217.90')),
    ('SE', Decimal('249.90')),
    ('TO', Decimal('219.90')),
]


def seed_inteiro_teor(apps, schema_editor):
    State = apps.get_model('products', 'State')
    PrecoImovelEstado = apps.get_model('products', 'PrecoImovelEstado')

    for uf, price in PRECOS_INTEIRO_TEOR:
        state = State.objects.filter(code=uf).first()
        if not state:
            continue
        obj, created = PrecoImovelEstado.objects.get_or_create(
            tipo_certidao='inteiro_teor',
            state=state,
            defaults={'price': price, 'is_active': True},
        )
        if not created and obj.price != price:
            obj.price = price
            obj.save(update_fields=['price'])


def unseed_inteiro_teor(apps, schema_editor):
    PrecoImovelEstado = apps.get_model('products', 'PrecoImovelEstado')
    PrecoImovelEstado.objects.filter(tipo_certidao='inteiro_teor').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_remove_precoimovelestado_unique_tipo_certidao_state_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_inteiro_teor, reverse_code=unseed_inteiro_teor),
    ]
