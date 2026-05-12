from django.db import migrations, models


TIPO_CERTIDAO_PARA_CATEGORIA = {
    'nascimento':               'registro_civil',
    'casamento':                'registro_civil',
    'obito':                    'registro_civil',
    'interdicao':               'registro_civil',
    'procuracao':               'notas',
    'escritura':                'notas',
    'uniao_estavel':            'notas',
    'escritura_ata_notarial':   'notas',
    'escritura_compra_venda':   'notas',
    'escritura_divorcio':       'notas',
    'escritura_doacao':         'notas',
    'escritura_emancipacao':    'notas',
    'escritura_hipoteca':       'notas',
    'escritura_inventario':     'notas',
    'escritura_pacto_antenupcial': 'notas',
    'escritura_permuta':        'notas',
    'escritura_testamento':     'notas',
    'imovel':                   'imoveis',
    'cnd_federal':              'federais_estaduais',
    'outros':                   'outros',
}


def populate_categoria_painel(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    to_update = []
    for order in Order.objects.all().only('id', 'tipo_certidao', 'categoria_painel'):
        cat = TIPO_CERTIDAO_PARA_CATEGORIA.get(order.tipo_certidao, 'outros')
        order.categoria_painel = cat
        to_update.append(order)
    if to_update:
        Order.objects.bulk_update(to_update, ['categoria_painel'], batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_alter_order_tipo_certidao_escritura_variantes'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='categoria_painel',
            field=models.CharField(
                blank=True,
                choices=[
                    ('registro_civil',     'Registro Civil'),
                    ('notas',              'Tabelionato de Notas'),
                    ('imoveis',            'Registro de Imóveis'),
                    ('protestos',          'Tabelionato de Protestos'),
                    ('federais_estaduais', 'Federais e Estaduais'),
                    ('busca',              'Busca'),
                    ('apostilamento',      'Apostilamento'),
                    ('outros',             'Outros'),
                ],
                db_index=True,
                max_length=30,
                verbose_name='Categoria do Painel',
            ),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(
                fields=['categoria_painel', '-created_at'],
                name='orders_order_cat_created_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(
                fields=['categoria_painel', 'status'],
                name='orders_order_cat_status_idx',
            ),
        ),
        migrations.RunPython(populate_categoria_painel, migrations.RunPython.noop),
    ]
