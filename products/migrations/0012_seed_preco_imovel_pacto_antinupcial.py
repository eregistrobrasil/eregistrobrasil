"""
Data migration: seed dos preços de Pacto Antinupcial por estado.
Chave interna: 'pacto_antinupcial', conforme definido em TIPOS_CERTIDAO_IMOVEL.
Idempotente: get_or_create + atualiza se divergir.
"""
from decimal import Decimal
from django.db import migrations


PRECOS_PACTO_ANTINUPCIAL = [
    ('AC', Decimal('160.65')),
    ('AL', Decimal('169.90')),
    ('AP', Decimal('179.90')),
    ('AM', Decimal('219.90')),
    ('BA', Decimal('699.90')),
    ('CE', Decimal('699.90')),
    ('ES', Decimal('229.90')),
    ('DF', Decimal('249.90')),
    ('GO', Decimal('249.90')),
    ('MA', Decimal('699.90')),
    ('MT', Decimal('189.90')),
    ('MS', Decimal('229.90')),
    ('MG', Decimal('229.90')),
    ('PA', Decimal('349.90')),
    ('PB', Decimal('249.90')),
    ('PR', Decimal('229.90')),
    ('PE', Decimal('189.90')),
    ('PI', Decimal('192.08')),
    ('RJ', Decimal('259.90')),
    ('RN', Decimal('699.90')),
    ('RS', Decimal('199.90')),
    ('RO', Decimal('219.90')),
    ('RR', Decimal('199.90')),
    ('SC', Decimal('199.90')),
    ('SP', Decimal('217.90')),
    ('SE', Decimal('149.90')),
    ('TO', Decimal('149.90')),
]


def seed_pacto_antinupcial(apps, schema_editor):
    State = apps.get_model('products', 'State')
    PrecoImovelEstado = apps.get_model('products', 'PrecoImovelEstado')

    for uf, price in PRECOS_PACTO_ANTINUPCIAL:
        state = State.objects.filter(code=uf).first()
        if not state:
            continue
        obj, created = PrecoImovelEstado.objects.get_or_create(
            tipo_certidao='pacto_antinupcial',
            state=state,
            defaults={'price': price, 'is_active': True},
        )
        if not created and obj.price != price:
            obj.price = price
            obj.save(update_fields=['price'])


def unseed_pacto_antinupcial(apps, schema_editor):
    PrecoImovelEstado = apps.get_model('products', 'PrecoImovelEstado')
    PrecoImovelEstado.objects.filter(tipo_certidao='pacto_antinupcial').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_seed_preco_imovel_doc_arquivado'),
    ]

    operations = [
        migrations.RunPython(seed_pacto_antinupcial, reverse_code=unseed_pacto_antinupcial),
    ]
