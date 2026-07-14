"""
Serviços de domínio do módulo financeiro.

Geração automática de lançamentos a partir de vendas (Orders pagas),
sem alterar a lógica de pagamentos existente.
"""
import logging

from django.db import transaction
from django.utils import timezone

from financeiro.models import ContaContabil, Lancamento, ServicoContaReceita

logger = logging.getLogger(__name__)

# Status de Order que representam venda efetivada (pagamento aprovado ou fases posteriores)
STATUS_VENDA_EFETIVADA = (
    'paid', 'novo', 'em_analise', 'aguardando_documentos', 'em_processamento',
    'em_cartorio', 'pronto_envio', 'enviado', 'concluido', 'processing', 'completed',
)

# Status que anulam a venda
STATUS_VENDA_CANCELADA = ('cancelado', 'refunded')

CONTA_RECEITA_FALLBACK_CODIGO = '1.1.99'  # Outros Serviços


def get_conta_receita_para_produto(product):
    """Resolve a conta de receita de um produto (vínculo ou fallback)."""
    vinculo = ServicoContaReceita.objects.filter(service=product).select_related('conta').first()
    if vinculo and vinculo.conta.is_active:
        return vinculo.conta
    return ContaContabil.objects.filter(
        codigo=CONTA_RECEITA_FALLBACK_CODIGO, tipo='receita', natureza='analitica',
    ).first()


def _mapear_forma_pagamento(order):
    metodo = (order.payment_method or '').lower()
    if 'pix' in metodo:
        return 'pix'
    if 'credit' in metodo or 'crédito' in metodo or 'credito' in metodo:
        return 'cartao_credito'
    if 'debit' in metodo or 'débito' in metodo or 'debito' in metodo:
        return 'cartao_debito'
    if 'boleto' in metodo or 'ticket' in metodo:
        return 'boleto'
    if metodo:
        return 'outro'
    return ''


@transaction.atomic
def gerar_lancamentos_venda(order, data_competencia=None):
    """
    Cria lançamentos de receita para uma Order paga — um por item, vinculado
    à conta de receita do serviço. Idempotente: não duplica se já existirem.

    Retorna a quantidade de lançamentos criados.
    """
    if Lancamento.objects.filter(order=order, origem='venda').exists():
        return 0

    data = data_competencia or timezone.localdate()
    forma = _mapear_forma_pagamento(order)
    criados = 0

    itens = list(order.items.select_related('product', 'product__category'))
    if itens:
        for item in itens:
            conta = get_conta_receita_para_produto(item.product) if item.product else None
            if conta is None:
                conta = ContaContabil.objects.filter(
                    codigo=CONTA_RECEITA_FALLBACK_CODIGO,
                ).first()
            if conta is None:
                logger.warning(
                    'Plano de contas sem conta fallback (%s); lançamento da venda %s não gerado.',
                    CONTA_RECEITA_FALLBACK_CODIGO, order.short_id,
                )
                return criados
            Lancamento.objects.create(
                tipo='receita',
                conta=conta,
                descricao=f'Venda #{order.short_id} — {item.product_name}',
                valor=item.get_total(),
                data_competencia=data,
                data_pagamento=data,
                status='confirmado',
                forma_pagamento=forma,
                origem='venda',
                order=order,
                observacoes=f'Gerado automaticamente a partir do pedido {order.short_id}.',
            )
            criados += 1
    elif order.total and order.total > 0:
        # Pedido sem itens: um lançamento único com o total
        conta = ContaContabil.objects.filter(codigo=CONTA_RECEITA_FALLBACK_CODIGO).first()
        if conta is None:
            logger.warning(
                'Plano de contas sem conta fallback (%s); lançamento da venda %s não gerado.',
                CONTA_RECEITA_FALLBACK_CODIGO, order.short_id,
            )
            return criados
        Lancamento.objects.create(
            tipo='receita',
            conta=conta,
            descricao=f'Venda #{order.short_id}',
            valor=order.total,
            data_competencia=data,
            data_pagamento=data,
            status='confirmado',
            forma_pagamento=forma,
            origem='venda',
            order=order,
            observacoes=f'Gerado automaticamente a partir do pedido {order.short_id}.',
        )
        criados = 1

    return criados


def cancelar_lancamentos_venda(order):
    """Cancela lançamentos automáticos de uma venda cancelada/reembolsada."""
    return (
        Lancamento.objects
        .filter(order=order, origem='venda')
        .exclude(status='cancelado')
        .update(status='cancelado', updated_at=timezone.now())
    )


def sincronizar_lancamentos_order(order):
    """
    Ponto de entrada do signal: decide criar ou cancelar lançamentos
    conforme o status atual da Order.
    """
    if order.status in STATUS_VENDA_EFETIVADA:
        return gerar_lancamentos_venda(order)
    if order.status in STATUS_VENDA_CANCELADA:
        return cancelar_lancamentos_venda(order)
    return 0
