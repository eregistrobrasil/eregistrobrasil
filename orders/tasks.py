from celery import shared_task
from django.utils import timezone


@shared_task(name='orders.calcular_prioridade_automatica')
def calcular_prioridade_automatica():
    from .models import Order

    ativos = Order.objects.exclude(
        status__in=('concluido', 'cancelado', 'refunded', 'completed')
    ).exclude(prazo_entrega=None)

    atualizados = 0
    for order in ativos:
        nova_prioridade = _calcular_prioridade(order)
        if nova_prioridade != order.prioridade:
            Order.objects.filter(pk=order.pk).update(prioridade=nova_prioridade)
            atualizados += 1
    return f'{atualizados} prioridades recalculadas'


def _calcular_prioridade(order):
    horas = order.horas_restantes
    if horas is None:
        return order.prioridade

    # Atrasado ou < 4h → urgente
    if horas <= 0 or horas < 4:
        return 'urgente'
    # < 24h → alta
    if horas < 24:
        return 'alta'
    # < 48h → media
    if horas < 48:
        return 'media'
    return 'baixa'


@shared_task(name='orders.atualizar_status_apos_pagamento')
def atualizar_status_apos_pagamento(order_id):
    from .models import Order
    from notifications.tasks import enviar_email_status

    try:
        order = Order.objects.get(pk=order_id, status='paid')
    except Order.DoesNotExist:
        return 'Pedido não encontrado ou status inválido'

    order.registrar_log('novo', observacao='Status automático após pagamento aprovado')
    order.status = 'novo'
    order.definir_prazo_automatico()
    order.save(update_fields=['status', 'prazo_entrega', 'sla_horas'])

    enviar_email_status.delay(str(order_id), 'novo')
    return f'Pedido {order.short_id} → novo'
