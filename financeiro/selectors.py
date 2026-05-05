from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from orders.models import Order
from products.models import Product, Category


def get_metricas_gerais():
    hoje = timezone.now().date()
    inicio_hoje = timezone.make_aware(
        timezone.datetime.combine(hoje, timezone.datetime.min.time())
    )
    inicio_mes = timezone.make_aware(
        timezone.datetime(hoje.year, hoje.month, 1)
    )

    pagos_qs = Order.objects.filter(status__in=('paid', 'concluido', 'completed'))

    total_faturamento = pagos_qs.aggregate(v=Sum('total'))['v'] or Decimal('0')
    faturamento_hoje = pagos_qs.filter(
        created_at__gte=inicio_hoje
    ).aggregate(v=Sum('total'))['v'] or Decimal('0')
    faturamento_mes = pagos_qs.filter(
        created_at__gte=inicio_mes
    ).aggregate(v=Sum('total'))['v'] or Decimal('0')

    total_pedidos = Order.objects.count()
    ticket_medio = pagos_qs.aggregate(v=Avg('total'))['v'] or Decimal('0')

    por_status = {}
    for status, label in Order.STATUS_CHOICES:
        count = Order.objects.filter(status=status).count()
        if count:
            por_status[label] = count

    return {
        'total_faturamento': total_faturamento,
        'faturamento_hoje': faturamento_hoje,
        'faturamento_mes': faturamento_mes,
        'total_pedidos': total_pedidos,
        'ticket_medio': ticket_medio,
        'por_status': por_status,
        'pedidos_pagos': pagos_qs.count(),
        'pedidos_pendentes': Order.objects.filter(status='pending').count(),
        'pedidos_cancelados': Order.objects.filter(status__in=('cancelado', 'refunded')).count(),
    }


def get_faturamento_por_periodo(dias=30):
    inicio = timezone.now() - timedelta(days=dias)
    pedidos = (
        Order.objects
        .filter(status__in=('paid', 'concluido', 'completed'), created_at__gte=inicio)
        .extra(select={'dia': "DATE(created_at)"})
        .values('dia')
        .annotate(total=Sum('total'), quantidade=Count('id'))
        .order_by('dia')
    )
    return list(pedidos)


def get_ultimas_vendas(limit=15):
    return (
        Order.objects
        .filter(status__in=('paid', 'concluido', 'completed'))
        .select_related('user')
        .order_by('-created_at')[:limit]
    )


def get_servicos_mais_vendidos(limit=10):
    from orders.models import OrderItem
    try:
        return (
            OrderItem.objects
            .values('product__name', 'product__id')
            .annotate(total_vendido=Count('id'), receita=Sum('price'))
            .order_by('-total_vendido')[:limit]
        )
    except Exception:
        return []


def get_relatorio(data_inicio=None, data_fim=None, categoria_id=None):
    qs = Order.objects.filter(status__in=('paid', 'concluido', 'completed'))

    if data_inicio:
        qs = qs.filter(created_at__date__gte=data_inicio)
    if data_fim:
        qs = qs.filter(created_at__date__lte=data_fim)

    resumo = qs.aggregate(
        receita=Sum('total'),
        quantidade=Count('id'),
        ticket=Avg('total'),
    )
    return qs, resumo
