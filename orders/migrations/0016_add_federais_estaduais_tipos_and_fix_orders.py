"""
Migration 0016 — Federais e Estaduais

1. Adiciona novos valores em Order.tipo_certidao (ALTER COLUMN não é necessário pois
   o campo é CharField sem choices aplicadas ao DB — apenas validação no nível do ORM).
2. Corrige pedidos existentes cujos produtos pertencem à categoria federais_estaduais
   mas ainda estão com categoria_painel='outros' ou tipo_certidao desconhecido.
"""
from django.db import migrations


# Mapa slug → tipo_certidao (espelho do PRODUTO_SLUG_PARA_TIPO adicionado em models.py)
SLUG_TO_TIPO = {
    'cnd-federal-receita-federal':                              'cnd_federal',
    'certidao-negativa-federal':                                'cnd_federal',
    'certidao-negativa-estadual':                               'cnd_federal',
    'certidao-fgts-inss':                                       'fgts_inss',
    'certidao-fgtsinss':                                        'fgts_inss',
    'cnd-estadual-sefaz':                                       'cnd_estadual',
    'cnd-itr-receita-federal':                                  'cnd_itr',
    'cnj-improbidade-administrativa-e-inelegibilidade':         'cnj_improbidade',
    'cadastro-de-imoveis-rurais-cafir':                         'cafir',
    'certidao-ibama-certidao-de-embargos':                      'ibama_embargos',
    'certidao-negativa-de-acoes-criminais':                     'certidao_negativa_acoes_criminais',
    'certidao-negativa-de-debitos-ambientais':                  'certidao_negativa_debitos_ambientais',
    'certidao-negativa-municipio':                              'certidao_negativa_municipio',
    'certidao-de-cumprimento-da-cota-legal-de-pcds':            'cota_legal_pcds',
    'certidao-negativa-de-debitos-trabalhistas':                'debitos_trabalhistas',
    'certidao-de-propriedade-de-aeronave':                      'propriedade_aeronave',
    'junta-comercial-certidao-da-empresa':                      'junta_comercial',
    'certidao-regularidade-crea':                               'regularidade_crea',
    'certidao-antecedentes-criminais':                          'antecedentes_criminais',
    'certidao-de-antecedentes-criminais':                       'antecedentes_criminais',
    'tse-certidao-de-quitacao-eleitoral':                       'tse_quitacao_eleitoral',
    'certidao-negativa-de-debitos-do-ibama':                    'fed_estadual_outros',
    'certidao-de-distribuicao-estadual-civel-criminal-f':       'fed_estadual_outros',
    'certidao-de-distribuicao-da-justica-federal':              'fed_estadual_outros',
    'certidao-de-tributos-da-procuradoria-geral-do-esta':       'fed_estadual_outros',
    'mpe-certidao-de-inquerito-civil':                          'fed_estadual_outros',
    'mpe-certidao-de-inquerito-criminal':                       'fed_estadual_outros',
    'mpf-certidao-negativa':                                    'fed_estadual_outros',
    'mt-certidao-de-debitos':                                   'fed_estadual_outros',
    'mt-certidao-de-infracoes-trabalhistas':                    'fed_estadual_outros',
    'stf-certidao-distribuidor':                                'fed_estadual_outros',
    'stj-certidao-do-stj':                                      'fed_estadual_outros',
    'tcu-certidao-de-tribunal-de-contas':                       'fed_estadual_outros',
    'trt-certidao-de-acoes-trabalhistas-ceat':                  'fed_estadual_outros',
}

ALL_FED_EST_TIPOS = set(SLUG_TO_TIPO.values())


def fix_federais_estaduais_orders(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    OrderItem = apps.get_model('orders', 'OrderItem')

    # 1) Corrigir pedidos com tipo_certidao já mapeado mas categoria_painel errada
    Order.objects.filter(
        tipo_certidao__in=ALL_FED_EST_TIPOS,
    ).exclude(
        categoria_painel='federais_estaduais',
    ).update(categoria_painel='federais_estaduais')

    # 2) Para pedidos com tipo_certidao vazio/outros que têm itens com produtos
    #    da categoria federais_estaduais — derivar tipo do slug do produto
    for slug, tipo in SLUG_TO_TIPO.items():
        order_ids = (
            OrderItem.objects.filter(product__slug=slug)
            .values_list('order_id', flat=True)
            .distinct()
        )
        if not order_ids:
            continue
        # Atualizar categoria e tipo para pedidos que ainda não estão corretos
        Order.objects.filter(
            pk__in=order_ids,
        ).exclude(
            categoria_painel='federais_estaduais',
        ).update(
            categoria_painel='federais_estaduais',
            tipo_certidao=tipo,
        )
        # Também corrigir pedidos já na categoria mas sem tipo_certidao definido
        Order.objects.filter(
            pk__in=order_ids,
            tipo_certidao='',
        ).update(tipo_certidao=tipo)


def reverse_fix(apps, schema_editor):
    # Não revertemos dados — irreversível por segurança
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0015_alter_order_tipo_certidao_imoveis'),
    ]

    operations = [
        migrations.RunPython(fix_federais_estaduais_orders, reverse_fix),
    ]
