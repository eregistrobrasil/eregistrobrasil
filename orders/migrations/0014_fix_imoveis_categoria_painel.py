"""
Migração de dados: corrige pedidos de imóveis com categoria_painel incorreta.

Todos os pedidos cujo produto pertence à categoria 'imoveis' (pelo slug do produto)
mas que têm categoria_painel != 'imoveis' são atualizados em lote.
Também atribui tipo_certidao correto com base no PRODUTO_SLUG_PARA_TIPO.
"""
from django.db import migrations

PRODUTO_SLUG_PARA_TIPO_IMOVEIS = {
    'certidao-de-imovel':                              'imovel',
    'certidao-de-matricula-atualizada':                'imovel_matricula_atualizada',
    'certidao-negativa-de-alienacao-fiduciaria':       'imovel_alienacao_fiduciaria',
    'certidao-de-onus-reais':                          'imovel_onus_reais',
    'pesquisa-de-bens':                                'imovel_pesquisa_bens',
    'certidao-de-penhor-de-safra':                     'imovel_penhor_safra',
    'pacote-de-certidoes-compra-e-venda-de-imovel':    'imovel_pacote_compra_venda',
}


def fix_imoveis_orders(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    OrderItem = apps.get_model('orders', 'OrderItem')

    # Encontra IDs de pedidos que têm pelo menos um item de produto imóveis
    order_ids_com_produto = set(
        OrderItem.objects.filter(
            product__slug__in=PRODUTO_SLUG_PARA_TIPO_IMOVEIS.keys()
        ).values_list('order_id', flat=True)
    )

    if not order_ids_com_produto:
        return

    orders_to_fix = Order.objects.filter(
        id__in=order_ids_com_produto
    ).exclude(categoria_painel='imoveis')

    for order in orders_to_fix:
        order.categoria_painel = 'imoveis'
        # Se tipo_certidao ainda não foi definido, derivar pelo primeiro item de produto imóvel
        if not order.tipo_certidao or order.tipo_certidao == 'outros':
            item = OrderItem.objects.filter(
                order=order,
                product__slug__in=PRODUTO_SLUG_PARA_TIPO_IMOVEIS.keys()
            ).first()
            if item:
                order.tipo_certidao = PRODUTO_SLUG_PARA_TIPO_IMOVEIS.get(
                    item.product.slug, 'imovel'
                )
        order.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0013_alter_order_tipo_certidao'),
    ]

    operations = [
        migrations.RunPython(fix_imoveis_orders, noop),
    ]
