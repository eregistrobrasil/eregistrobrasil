"""
Migration 0019 — Fix apostilamento orders

Corrige pedidos existentes cujos produtos pertencem à categoria apostilamento
mas estão com categoria_painel='outros' ou tipo_certidao vazio/errado.
"""
from django.db import migrations


SLUG_TO_TIPO = {
    'apostila-de-haia':     'apostila_haia',
    'traducao-juramentada': 'traducao_juramentada',
}


def fix_apostilamento_orders(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    OrderItem = apps.get_model('orders', 'OrderItem')

    # Corrigir pelo tipo_certidao já existente
    Order.objects.filter(
        tipo_certidao__in=['apostila_haia', 'traducao_juramentada'],
    ).exclude(
        categoria_painel='apostilamento',
    ).update(categoria_painel='apostilamento')

    # Corrigir pelo slug do produto
    for slug, tipo in SLUG_TO_TIPO.items():
        order_ids = list(
            OrderItem.objects.filter(product__slug=slug)
            .values_list('order_id', flat=True)
            .distinct()
        )
        if not order_ids:
            continue
        Order.objects.filter(pk__in=order_ids).exclude(
            categoria_painel='apostilamento',
        ).update(categoria_painel='apostilamento', tipo_certidao=tipo)
        Order.objects.filter(pk__in=order_ids, tipo_certidao='').update(tipo_certidao=tipo)


def reverse_fix(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0018_alter_order_tipo_certidao'),
    ]

    operations = [
        migrations.RunPython(fix_apostilamento_orders, reverse_fix),
    ]
