from decimal import Decimal
from datetime import timedelta

from django.db.models import Sum, Count, Avg, Q, Min, Max
from django.db.models.functions import TruncMonth
from django.utils import timezone

from orders.models import Order
from products.models import Product, ServiceStatePrice
from financeiro.models import ContaContabil, Lancamento


# ─── Seletores baseados em Pedidos (relatórios de vendas) ─────────────────────

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


# ─── Seletores da Gestão Financeira (Lançamentos) ─────────────────────────────

def _lancamentos_validos():
    return Lancamento.objects.exclude(status='cancelado')


def get_kpis_financeiros():
    """KPIs principais do dashboard: mês atual, mês anterior e acumulado."""
    hoje = timezone.localdate()
    inicio_mes = hoje.replace(day=1)
    fim_mes_anterior = inicio_mes - timedelta(days=1)
    inicio_mes_anterior = fim_mes_anterior.replace(day=1)

    qs = _lancamentos_validos()

    def _soma(qs_filtrado, tipo):
        return qs_filtrado.filter(tipo=tipo).aggregate(v=Sum('valor'))['v'] or Decimal('0')

    mes_qs = qs.filter(data_competencia__gte=inicio_mes, data_competencia__lte=hoje)
    mes_ant_qs = qs.filter(
        data_competencia__gte=inicio_mes_anterior,
        data_competencia__lte=fim_mes_anterior,
    )

    receitas_mes = _soma(mes_qs, 'receita')
    despesas_mes = _soma(mes_qs, 'despesa')
    receitas_mes_ant = _soma(mes_ant_qs, 'receita')
    despesas_mes_ant = _soma(mes_ant_qs, 'despesa')

    receitas_total = _soma(qs, 'receita')
    despesas_total = _soma(qs, 'despesa')

    def _variacao(atual, anterior):
        if anterior and anterior > 0:
            return float((atual - anterior) / anterior * 100)
        return None

    resultado_mes = receitas_mes - despesas_mes
    resultado_mes_ant = receitas_mes_ant - despesas_mes_ant

    margem = None
    if receitas_mes > 0:
        margem = float(resultado_mes / receitas_mes * 100)

    pendentes = Lancamento.objects.filter(status='pendente')
    a_receber = pendentes.filter(tipo='receita').aggregate(v=Sum('valor'))['v'] or Decimal('0')
    a_pagar = pendentes.filter(tipo='despesa').aggregate(v=Sum('valor'))['v'] or Decimal('0')

    return {
        'receitas_mes': receitas_mes,
        'despesas_mes': despesas_mes,
        'resultado_mes': resultado_mes,
        'var_receitas': _variacao(receitas_mes, receitas_mes_ant),
        'var_despesas': _variacao(despesas_mes, despesas_mes_ant),
        'var_resultado': _variacao(resultado_mes, resultado_mes_ant),
        'margem_mes': margem,
        'receitas_total': receitas_total,
        'despesas_total': despesas_total,
        'saldo_acumulado': receitas_total - despesas_total,
        'a_receber': a_receber,
        'a_pagar': a_pagar,
    }


def get_serie_mensal(meses=12):
    """Série mensal de receitas x despesas para gráfico de barras."""
    hoje = timezone.localdate()
    inicio = (hoje.replace(day=1) - timedelta(days=(meses - 1) * 31)).replace(day=1)

    agregado = (
        _lancamentos_validos()
        .filter(data_competencia__gte=inicio)
        .annotate(mes=TruncMonth('data_competencia'))
        .values('mes', 'tipo')
        .annotate(total=Sum('valor'))
        .order_by('mes')
    )

    por_mes = {}
    for row in agregado:
        chave = row['mes'].strftime('%Y-%m')
        por_mes.setdefault(chave, {'receita': 0.0, 'despesa': 0.0})
        por_mes[chave][row['tipo']] = float(row['total'])

    labels, receitas, despesas = [], [], []
    ano, mes = inicio.year, inicio.month
    nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    for _ in range(meses):
        chave = f'{ano}-{mes:02d}'
        labels.append(f'{nomes_meses[mes - 1]}/{str(ano)[2:]}')
        dados = por_mes.get(chave, {'receita': 0.0, 'despesa': 0.0})
        receitas.append(dados['receita'])
        despesas.append(dados['despesa'])
        mes += 1
        if mes > 12:
            mes, ano = 1, ano + 1

    return {'labels': labels, 'receitas': receitas, 'despesas': despesas}


def get_fluxo_diario(dias=30):
    """Fluxo de caixa diário (receitas − despesas) dos últimos N dias."""
    hoje = timezone.localdate()
    inicio = hoje - timedelta(days=dias - 1)

    agregado = (
        _lancamentos_validos()
        .filter(data_competencia__gte=inicio, data_competencia__lte=hoje)
        .values('data_competencia', 'tipo')
        .annotate(total=Sum('valor'))
    )

    por_dia = {}
    for row in agregado:
        chave = row['data_competencia']
        por_dia.setdefault(chave, {'receita': 0.0, 'despesa': 0.0})
        por_dia[chave][row['tipo']] = float(row['total'])

    labels, saldos = [], []
    for i in range(dias):
        dia = inicio + timedelta(days=i)
        labels.append(dia.strftime('%d/%m'))
        dados = por_dia.get(dia, {'receita': 0.0, 'despesa': 0.0})
        saldos.append(dados['receita'] - dados['despesa'])

    return {'labels': labels, 'saldos': saldos}


def get_composicao_por_conta(tipo, meses=1, limit=8):
    """Composição de receitas ou despesas por conta (para gráfico doughnut)."""
    hoje = timezone.localdate()
    inicio = (hoje.replace(day=1) - timedelta(days=(meses - 1) * 31)).replace(day=1)

    rows = (
        _lancamentos_validos()
        .filter(tipo=tipo, data_competencia__gte=inicio)
        .values('conta__codigo', 'conta__nome')
        .annotate(total=Sum('valor'))
        .order_by('-total')[:limit]
    )
    return {
        'labels': [f"{r['conta__codigo']} {r['conta__nome']}" for r in rows],
        'valores': [float(r['total']) for r in rows],
    }


def get_ultimos_lancamentos(limit=10):
    return (
        Lancamento.objects
        .select_related('conta', 'order', 'criado_por')
        .order_by('-data_competencia', '-created_at')[:limit]
    )


def get_lancamentos_queryset(q=None, tipo=None, conta=None, status=None,
                             origem=None, data_inicio=None, data_fim=None):
    """QuerySet filtrado de lançamentos para a listagem."""
    qs = (
        Lancamento.objects
        .select_related('conta', 'order', 'criado_por')
        .order_by('-data_competencia', '-created_at')
    )
    if q:
        qs = qs.filter(Q(descricao__icontains=q) | Q(observacoes__icontains=q))
    if tipo:
        qs = qs.filter(tipo=tipo)
    if conta:
        qs = qs.filter(conta__in=conta.get_descendentes_ids())
    if status:
        qs = qs.filter(status=status)
    if origem:
        qs = qs.filter(origem=origem)
    if data_inicio:
        qs = qs.filter(data_competencia__gte=data_inicio)
    if data_fim:
        qs = qs.filter(data_competencia__lte=data_fim)
    return qs


def get_resumo_lancamentos(qs):
    """Totais de um queryset de lançamentos (para cabeçalho da listagem)."""
    validos = qs.exclude(status='cancelado')
    receitas = validos.filter(tipo='receita').aggregate(v=Sum('valor'))['v'] or Decimal('0')
    despesas = validos.filter(tipo='despesa').aggregate(v=Sum('valor'))['v'] or Decimal('0')
    return {
        'receitas': receitas,
        'despesas': despesas,
        'saldo': receitas - despesas,
        'quantidade': qs.count(),
    }


def get_arvore_plano_contas(tipo=None, incluir_inativas=True):
    """
    Plano de contas ordenado hierarquicamente (lista achatada com nível),
    com totais de lançamentos agregados por conta (incluindo descendentes).
    """
    qs = ContaContabil.objects.all().order_by('codigo')
    if tipo:
        qs = qs.filter(tipo=tipo)
    if not incluir_inativas:
        qs = qs.filter(is_active=True)

    contas = list(qs)
    por_parent = {}
    for conta in contas:
        por_parent.setdefault(conta.parent_id, []).append(conta)

    # Totais diretos por conta (ano corrente)
    inicio_ano = timezone.localdate().replace(month=1, day=1)
    totais = dict(
        _lancamentos_validos()
        .filter(data_competencia__gte=inicio_ano)
        .values_list('conta_id')
        .annotate(total=Sum('valor'))
    )
    contagem = dict(
        Lancamento.objects
        .values_list('conta_id')
        .annotate(qtd=Count('id'))
    )

    resultado = []

    def _total_recursivo(conta):
        total = totais.get(conta.pk, Decimal('0'))
        for filha in por_parent.get(conta.pk, []):
            total += _total_recursivo(filha)
        return total

    def _walk(parent_id, nivel):
        for conta in por_parent.get(parent_id, []):
            conta.nivel_cache = nivel
            conta.total_ano = _total_recursivo(conta)
            conta.qtd_lancamentos = contagem.get(conta.pk, 0)
            conta.tem_filhas = conta.pk in por_parent
            resultado.append(conta)
            _walk(conta.pk, nivel + 1)

    _walk(None, 0)

    # Contas órfãs (pai filtrado fora, ex.: filtro por tipo)
    ids_no_resultado = {c.pk for c in resultado}
    for conta in contas:
        if conta.pk not in ids_no_resultado and conta.parent_id not in {c.pk for c in contas}:
            conta.nivel_cache = 0
            conta.total_ano = _total_recursivo(conta)
            conta.qtd_lancamentos = contagem.get(conta.pk, 0)
            conta.tem_filhas = conta.pk in por_parent
            resultado.append(conta)
            _walk(conta.pk, 1)

    return resultado
