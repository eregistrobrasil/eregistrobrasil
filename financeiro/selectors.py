from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q, Min, Max
from django.utils import timezone
from datetime import timedelta

from orders.models import Order
from products.models import Product, Category, ServiceStatePrice


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


# ─── Seletores do módulo Preços por Estado ────────────────────────────────────

def get_precos_queryset(q=None, servico=None, categoria=None, estado=None,
                        ativo=None, preco_min=None, preco_max=None):
    """
    Retorna QuerySet filtrado de ServiceStatePrice com select/prefetch otimizados.
    """
    qs = (
        ServiceStatePrice.objects
        .select_related('service', 'service__category', 'state')
        .order_by('service__category__order', 'service__order', 'service__name', 'state__name')
    )
    if q:
        qs = qs.filter(
            Q(service__name__icontains=q) |
            Q(service__category__name__icontains=q) |
            Q(state__name__icontains=q) |
            Q(state__code__icontains=q)
        )
    if servico:
        qs = qs.filter(service=servico)
    if categoria:
        qs = qs.filter(service__category=categoria)
    if estado:
        qs = qs.filter(state__code=estado.upper())
    if ativo == '1':
        qs = qs.filter(is_active=True)
    elif ativo == '0':
        qs = qs.filter(is_active=False)
    if preco_min is not None:
        qs = qs.filter(price__gte=preco_min)
    if preco_max is not None:
        qs = qs.filter(price__lte=preco_max)
    return qs


def get_metricas_precos():
    """Estatísticas resumidas para o dashboard de preços."""
    total = ServiceStatePrice.objects.count()
    ativos = ServiceStatePrice.objects.filter(is_active=True).count()
    inativos = total - ativos

    servicos_com_preco = (
        ServiceStatePrice.objects
        .values('service_id')
        .distinct()
        .count()
    )
    total_servicos = Product.objects.filter(is_active=True).count()
    servicos_sem_preco = total_servicos - servicos_com_preco

    agg = ServiceStatePrice.objects.filter(is_active=True).aggregate(
        preco_medio=Avg('price'),
        preco_min=Min('price'),
        preco_max=Max('price'),
    )

    return {
        'total': total,
        'ativos': ativos,
        'inativos': inativos,
        'servicos_com_preco': servicos_com_preco,
        'total_servicos': total_servicos,
        'servicos_sem_preco': servicos_sem_preco,
        'preco_medio': agg['preco_medio'] or Decimal('0'),
        'preco_min': agg['preco_min'] or Decimal('0'),
        'preco_max': agg['preco_max'] or Decimal('0'),
    }



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
