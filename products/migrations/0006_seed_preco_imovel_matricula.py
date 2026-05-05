"""
Data migration: seed dos preços de Matrícula (certidão de imóvel) por estado.
Usa get_or_create para ser idempotente (pode ser re-executada com segurança).
"""
from decimal import Decimal
from django.db import migrations


PRECOS_MATRICULA = [
    ('AC', Decimal('180.65')),
    ('AL', Decimal('169.90')),
    ('AP', Decimal('176.90')),
    ('AM', Decimal('241.89')),
    ('BA', Decimal('249.90')),
    ('CE', Decimal('149.90')),
    ('ES', Decimal('229.95')),
    ('DF', Decimal('122.88')),
    ('GO', Decimal('249.90')),
    ('MA', Decimal('219.90')),
    ('MT', Decimal('149.90')),
    ('MS', Decimal('129.90')),
    ('MG', Decimal('209.90')),
    ('PA', Decimal('169.90')),
    ('PB', Decimal('248.95')),
    ('PR', Decimal('229.90')),
    ('PE', Decimal('169.90')),
    ('PI', Decimal('189.90')),
    ('RJ', Decimal('299.90')),
    ('RN', Decimal('319.90')),
    ('RS', Decimal('199.90')),
    ('RO', Decimal('139.90')),
    ('RR', Decimal('119.90')),
    ('SC', Decimal('189.90')),
    ('SP', Decimal('199.90')),
    ('SE', Decimal('149.90')),
    ('TO', Decimal('149.90')),
]


def seed_matricula(apps, schema_editor):
    State = apps.get_model('products', 'State')
    PrecoImovelEstado = apps.get_model('products', 'PrecoImovelEstado')

    for uf, price in PRECOS_MATRICULA:
        state = State.objects.filter(code=uf).first()
        if not state:
            continue
        obj, created = PrecoImovelEstado.objects.get_or_create(
            tipo_certidao='matricula',
            state=state,
            defaults={'price': price, 'is_active': True},
        )
        if not created and obj.price != price:
            obj.price = price
            obj.save(update_fields=['price'])


def unseed_matricula(apps, schema_editor):
    PrecoImovelEstado = apps.get_model('products', 'PrecoImovelEstado')
    PrecoImovelEstado.objects.filter(tipo_certidao='matricula').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_precoimovelestado'),
    ]

    operations = [
        migrations.RunPython(seed_matricula, reverse_code=unseed_matricula),
    ]
