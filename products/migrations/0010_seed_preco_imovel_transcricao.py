"""
Data migration: seed dos preços de Transcrição por estado.
Chave interna: 'transcricao', conforme definido em TIPOS_CERTIDAO_IMOVEL.
Idempotente: get_or_create + atualiza se divergir.
"""
from decimal import Decimal
from django.db import migrations


PRECOS_TRANSCRICAO = [
    ('AC', Decimal('160.65')),
    ('AL', Decimal('169.90')),
    ('AP', Decimal('699.90')),
    ('AM', Decimal('239.90')),
    ('BA', Decimal('249.90')),
    ('CE', Decimal('149.90')),
    ('ES', Decimal('189.90')),
    ('DF', Decimal('122.88')),
    ('GO', Decimal('249.90')),
    ('MA', Decimal('199.90')),
    ('MT', Decimal('189.90')),
    ('MS', Decimal('129.90')),
    ('MG', Decimal('109.90')),
    ('PA', Decimal('318.89')),
    ('PB', Decimal('285.95')),
    ('PR', Decimal('229.90')),
    ('PE', Decimal('185.90')),
    ('PI', Decimal('189.90')),
    ('RJ', Decimal('237.90')),
    ('RN', Decimal('319.90')),
    ('RS', Decimal('199.90')),
    ('RO', Decimal('139.90')),
    ('RR', Decimal('119.90')),
    ('SC', Decimal('159.90')),
    ('SP', Decimal('229.90')),
    ('SE', Decimal('149.90')),
    ('TO', Decimal('149.90')),
]


def seed_transcricao(apps, schema_editor):
    State = apps.get_model('products', 'State')
    PrecoImovelEstado = apps.get_model('products', 'PrecoImovelEstado')

    for uf, price in PRECOS_TRANSCRICAO:
        state = State.objects.filter(code=uf).first()
        if not state:
            continue
        obj, created = PrecoImovelEstado.objects.get_or_create(
            tipo_certidao='transcricao',
            state=state,
            defaults={'price': price, 'is_active': True},
        )
        if not created and obj.price != price:
            obj.price = price
            obj.save(update_fields=['price'])


def unseed_transcricao(apps, schema_editor):
    PrecoImovelEstado = apps.get_model('products', 'PrecoImovelEstado')
    PrecoImovelEstado.objects.filter(tipo_certidao='transcricao').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_seed_preco_imovel_vintenaria'),
    ]

    operations = [
        migrations.RunPython(seed_transcricao, reverse_code=unseed_transcricao),
    ]
