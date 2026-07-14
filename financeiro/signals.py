"""
Signals do módulo financeiro.

Escuta o pós-save de Order para gerar/cancelar lançamentos automaticamente,
sem alterar a lógica de pagamentos (payments continua intacto).
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='orders.Order', dispatch_uid='financeiro_sync_lancamentos')
def sincronizar_financeiro_apos_save(sender, instance, **kwargs):
    from financeiro import services
    try:
        services.sincronizar_lancamentos_order(instance)
    except Exception:
        # Nunca interrompe o fluxo de pagamento por erro no financeiro
        logger.exception(
            'Falha ao sincronizar lançamentos financeiros do pedido %s', instance.pk
        )
