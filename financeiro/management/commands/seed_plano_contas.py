"""
Seed do Plano de Contas padrão da e-Registro Brasil.

- Cria a estrutura hierárquica de contas de receita e despesa (idempotente);
- Vincula todos os serviços existentes às contas de receita conforme a categoria;
- (--backfill) Gera lançamentos para vendas já pagas que ainda não possuem.

Uso:
    python manage.py seed_plano_contas
    python manage.py seed_plano_contas --backfill
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from financeiro.models import ContaContabil, ServicoContaReceita
from products.models import Product


# (codigo, nome, tipo, natureza, codigo_pai)
PLANO_PADRAO = [
    # ── RECEITAS ──────────────────────────────────────────────────────────
    ('1',      'Receitas',                          'receita', 'sintetica', None),
    ('1.1',    'Receita de Serviços',               'receita', 'sintetica', '1'),
    ('1.1.01', 'Registro Civil',                    'receita', 'analitica', '1.1'),
    ('1.1.02', 'Tabelionato de Notas',              'receita', 'analitica', '1.1'),
    ('1.1.03', 'Registro de Imóveis',               'receita', 'analitica', '1.1'),
    ('1.1.04', 'Protestos',                         'receita', 'analitica', '1.1'),
    ('1.1.05', 'Federais e Estaduais',              'receita', 'analitica', '1.1'),
    ('1.1.06', 'Busca e Pesquisa',                  'receita', 'analitica', '1.1'),
    ('1.1.07', 'Apostilamento e Tradução',          'receita', 'analitica', '1.1'),
    ('1.1.99', 'Outros Serviços',                   'receita', 'analitica', '1.1'),
    ('1.2',    'Outras Receitas',                   'receita', 'sintetica', '1'),
    ('1.2.01', 'Receitas Financeiras',              'receita', 'analitica', '1.2'),
    ('1.2.99', 'Receitas Diversas',                 'receita', 'analitica', '1.2'),
    # ── DESPESAS ──────────────────────────────────────────────────────────
    ('2',      'Despesas',                          'despesa', 'sintetica', None),
    ('2.1',    'Custos dos Serviços',               'despesa', 'sintetica', '2'),
    ('2.1.01', 'Emolumentos de Cartório',           'despesa', 'analitica', '2.1'),
    ('2.1.02', 'Taxas de Gateway de Pagamento',     'despesa', 'analitica', '2.1'),
    ('2.1.03', 'Envio e Logística',                 'despesa', 'analitica', '2.1'),
    ('2.1.99', 'Outros Custos de Serviços',         'despesa', 'analitica', '2.1'),
    ('2.2',    'Despesas Administrativas',          'despesa', 'sintetica', '2'),
    ('2.2.01', 'Pessoal e Pró-labore',              'despesa', 'analitica', '2.2'),
    ('2.2.02', 'Software e Assinaturas',            'despesa', 'analitica', '2.2'),
    ('2.2.03', 'Contabilidade e Jurídico',          'despesa', 'analitica', '2.2'),
    ('2.2.04', 'Infraestrutura e Hospedagem',       'despesa', 'analitica', '2.2'),
    ('2.2.99', 'Outras Despesas Administrativas',   'despesa', 'analitica', '2.2'),
    ('2.3',    'Despesas Comerciais',               'despesa', 'sintetica', '2'),
    ('2.3.01', 'Marketing e Publicidade',           'despesa', 'analitica', '2.3'),
    ('2.3.02', 'Comissões e Parcerias',             'despesa', 'analitica', '2.3'),
    ('2.4',    'Impostos e Tributos',               'despesa', 'sintetica', '2'),
    ('2.4.01', 'Impostos sobre Vendas',             'despesa', 'analitica', '2.4'),
    ('2.4.99', 'Outros Tributos',                   'despesa', 'analitica', '2.4'),
]

# Categoria de produto → código da conta de receita
CATEGORIA_PARA_CONTA = {
    'Registro Civil':           '1.1.01',
    'Notas':                    '1.1.02',
    'Imóveis':                  '1.1.03',
    'Protesto':                 '1.1.04',
    'Protestos':                '1.1.04',
    'Federais e Estaduais':     '1.1.05',
    'Busca':                    '1.1.06',
    'Pesquisa':                 '1.1.06',
    'Apostilamento':            '1.1.07',
    'Tradução e Apostilamento': '1.1.07',
}

CONTA_FALLBACK = '1.1.99'


class Command(BaseCommand):
    help = 'Cria o plano de contas padrão e vincula os serviços às contas de receita.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backfill', action='store_true',
            help='Gera lançamentos para vendas pagas sem lançamento.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        criadas = 0
        for codigo, nome, tipo, natureza, codigo_pai in PLANO_PADRAO:
            parent = ContaContabil.objects.filter(codigo=codigo_pai).first() if codigo_pai else None
            conta, created = ContaContabil.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nome': nome,
                    'tipo': tipo,
                    'natureza': natureza,
                    'parent': parent,
                    'is_system': True,
                },
            )
            if created:
                criadas += 1
        self.stdout.write(self.style.SUCCESS(
            f'Plano de contas: {criadas} conta(s) criada(s), '
            f'{len(PLANO_PADRAO) - criadas} já existiam.'
        ))

        # ── Vincula serviços às contas de receita ──────────────────────────
        contas = {c.codigo: c for c in ContaContabil.objects.filter(tipo='receita')}
        fallback = contas[CONTA_FALLBACK]

        vinculados = ja_vinculados = 0
        for produto in Product.objects.select_related('category'):
            conta = contas.get(
                CATEGORIA_PARA_CONTA.get(produto.category.name, CONTA_FALLBACK),
                fallback,
            )
            _, created = ServicoContaReceita.objects.get_or_create(
                service=produto, defaults={'conta': conta},
            )
            if created:
                vinculados += 1
            else:
                ja_vinculados += 1
        self.stdout.write(self.style.SUCCESS(
            f'Vínculos: {vinculados} serviço(s) vinculado(s), {ja_vinculados} já possuíam vínculo.'
        ))

        # ── Backfill de lançamentos para vendas já pagas ────────────────────
        if options['backfill']:
            from financeiro.services import (
                gerar_lancamentos_venda, STATUS_VENDA_EFETIVADA,
            )
            from orders.models import Order

            pedidos = Order.objects.filter(status__in=STATUS_VENDA_EFETIVADA)
            total_lancamentos = pedidos_processados = 0
            for order in pedidos.iterator():
                criados_qtd = gerar_lancamentos_venda(
                    order, data_competencia=order.created_at.date(),
                )
                if criados_qtd:
                    pedidos_processados += 1
                    total_lancamentos += criados_qtd
            self.stdout.write(self.style.SUCCESS(
                f'Backfill: {total_lancamentos} lançamento(s) gerado(s) '
                f'para {pedidos_processados} pedido(s).'
            ))
