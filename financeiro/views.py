import csv
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from accounts.permissions import staff_required, permission_required
from financeiro import selectors
from financeiro.forms import (
    ProductForm, PriceUpdateForm, RelatorioFilterForm, ServicoFilterForm,
    ServiceStatePriceForm, PrecoFilterForm, MassUpdateForm, ReplicarPrecosForm,
    ContaContabilForm, LancamentoForm, LancamentoFilterForm, VincularServicoContaForm,
)
from financeiro.models import (
    PriceHistory, StatePriceHistory,
    ContaContabil, Lancamento, ServicoContaReceita,
)
from products.models import Product, Category, State, ServiceStatePrice, ESTADOS_BR


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class FinanceiroDashboardView(View):
    template_name = 'financeiro/dashboard.html'

    def get(self, request):
        kpis = selectors.get_kpis_financeiros()
        serie_mensal = selectors.get_serie_mensal(12)
        fluxo_diario = selectors.get_fluxo_diario(30)
        composicao_receitas = selectors.get_composicao_por_conta('receita', meses=1)
        composicao_despesas = selectors.get_composicao_por_conta('despesa', meses=1)
        metricas = selectors.get_metricas_gerais()

        ctx = {
            'title': 'Dashboard Financeiro',
            'kpis': kpis,
            'metricas': metricas,
            'ultimos_lancamentos': selectors.get_ultimos_lancamentos(8),
            'ultimas_vendas': selectors.get_ultimas_vendas(8),
            'chart_mensal': json.dumps(serie_mensal),
            'chart_fluxo': json.dumps(fluxo_diario),
            'chart_receitas': json.dumps(composicao_receitas),
            'chart_despesas': json.dumps(composicao_despesas),
        }
        return render(request, self.template_name, ctx)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class ServicoListView(View):
    template_name = 'financeiro/servicos.html'

    def get(self, request):
        form = ServicoFilterForm(request.GET)
        estado_code = request.GET.get('estado', '').strip().upper()

        if estado_code:
            # Visão por estado: exibe ServiceStatePrice
            qs = (
                ServiceStatePrice.objects
                .filter(state__code=estado_code)
                .select_related('service', 'service__category', 'state')
                .order_by('service__category__order', 'service__order', 'service__name')
            )
            if form.is_valid():
                q = form.cleaned_data.get('q')
                categoria = form.cleaned_data.get('categoria')
                ativo = form.cleaned_data.get('ativo')
                if q:
                    qs = qs.filter(service__name__icontains=q)
                if categoria:
                    qs = qs.filter(service__category=categoria)
                if ativo == '1':
                    qs = qs.filter(is_active=True)
                elif ativo == '0':
                    qs = qs.filter(is_active=False)
            modo = 'estado'
            total = qs.count()
        else:
            # Visão padrão: lista produtos
            qs = Product.objects.select_related('category', 'tipo').order_by('category__order', 'order', 'name')
            if form.is_valid():
                q = form.cleaned_data.get('q')
                categoria = form.cleaned_data.get('categoria')
                ativo = form.cleaned_data.get('ativo')
                if q:
                    qs = qs.filter(name__icontains=q)
                if categoria:
                    qs = qs.filter(category=categoria)
                if ativo == '1':
                    qs = qs.filter(is_active=True)
                elif ativo == '0':
                    qs = qs.filter(is_active=False)
            modo = 'geral'
            total = qs.count()

        from products.models import ESTADOS_BR
        ctx = {
            'title': 'Gestão de Serviços',
            'servicos': qs,
            'form': form,
            'total': total,
            'modo': modo,
            'estado_code': estado_code,
            'estados': ESTADOS_BR,
        }
        return render(request, self.template_name, ctx)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class ServicoCreateView(View):
    """Criação manual de serviços foi desativada — serviços são gerenciados pelo sistema."""

    def get(self, request):
        messages.warning(request, 'A criação manual de serviços foi desativada. Os serviços são gerenciados pelo sistema.')
        return redirect('financeiro:servicos')

    def post(self, request):
        messages.warning(request, 'A criação manual de serviços foi desativada.')
        return redirect('financeiro:servicos')


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class ServicoEditView(View):
    template_name = 'financeiro/servico_form.html'

    def get(self, request, pk):
        servico = get_object_or_404(Product, pk=pk)
        form = ProductForm(instance=servico)
        historico = PriceHistory.objects.filter(product=servico).select_related('alterado_por')[:10]
        ctx = {
            'title': f'Editar: {servico.name}',
            'form': form,
            'servico': servico,
            'historico': historico,
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        servico = get_object_or_404(Product, pk=pk)
        preco_anterior = servico.price
        form = ProductForm(request.POST, instance=servico)
        if form.is_valid():
            servico_atualizado = form.save()
            if servico_atualizado.price != preco_anterior:
                PriceHistory.objects.create(
                    product=servico_atualizado,
                    preco_anterior=preco_anterior,
                    preco_novo=servico_atualizado.price,
                    alterado_por=request.user,
                )
            messages.success(request, f'Serviço "{servico_atualizado.name}" atualizado.')
            return redirect('financeiro:servicos')
        historico = PriceHistory.objects.filter(product=servico).select_related('alterado_por')[:10]
        ctx = {
            'title': f'Editar: {servico.name}',
            'form': form,
            'servico': servico,
            'historico': historico,
        }
        return render(request, self.template_name, ctx)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class ServicoDeleteView(View):
    def post(self, request, pk):
        servico = get_object_or_404(Product, pk=pk)
        if servico.is_system_service:
            messages.error(request, f'O serviço "{servico.name}" é um serviço do sistema e não pode ser excluído.')
            return redirect('financeiro:servicos')
        nome = servico.name
        servico.delete()
        messages.success(request, f'Serviço "{nome}" excluído.')
        return redirect('financeiro:servicos')


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class StatePriceInlineUpdateView(View):
    """Atualização de preço por estado via AJAX."""

    def post(self, request, pk):
        ssp = get_object_or_404(ServiceStatePrice, pk=pk)
        form = PriceUpdateForm(request.POST)
        if form.is_valid():
            preco_anterior = ssp.price
            novo_preco = form.cleaned_data['price']
            preco_promo = form.cleaned_data.get('original_price')

            if novo_preco != preco_anterior:
                PriceHistory.objects.create(
                    product=ssp.service,
                    preco_anterior=preco_anterior,
                    preco_novo=novo_preco,
                    alterado_por=request.user,
                )
                ssp.price = novo_preco

            if preco_promo is not None:
                ssp.promotional_price = preco_promo

            ssp.save(update_fields=['price', 'promotional_price'])
            return JsonResponse({'ok': True, 'price': str(ssp.price)})
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class StatePriceToggleView(View):
    def post(self, request, pk):
        ssp = get_object_or_404(ServiceStatePrice, pk=pk)
        ssp.is_active = not ssp.is_active
        ssp.save(update_fields=['is_active'])
        return JsonResponse({'ok': True, 'is_active': ssp.is_active})


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class BulkPriceUpdateView(View):
    """Copia preço de um serviço para todos os estados selecionados."""

    def post(self, request):
        service_id = request.POST.get('service_id')
        price = request.POST.get('price')
        estados = request.POST.getlist('estados')

        if not all([service_id, price, estados]):
            messages.error(request, 'Dados incompletos para atualização em massa.')
            return redirect('financeiro:servicos')

        service = get_object_or_404(Product, pk=service_id)
        from decimal import Decimal
        try:
            novo_preco = Decimal(price)
        except Exception:
            messages.error(request, 'Preço inválido.')
            return redirect('financeiro:servicos')

        updated = (
            ServiceStatePrice.objects
            .filter(service=service, state__code__in=estados)
            .update(price=novo_preco)
        )
        messages.success(request, f'{updated} estado(s) atualizados para R$ {novo_preco}.')
        return redirect(f'{request.META.get("HTTP_REFERER", "/financeiro/servicos/")}')


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class PriceInlineUpdateView(View):
    """Atualização de preço via AJAX na listagem."""

    def post(self, request, pk):
        servico = get_object_or_404(Product, pk=pk)
        form = PriceUpdateForm(request.POST)
        if form.is_valid():
            preco_anterior = servico.price
            novo_preco = form.cleaned_data['price']
            preco_promo = form.cleaned_data.get('original_price')

            if novo_preco != preco_anterior:
                PriceHistory.objects.create(
                    product=servico,
                    preco_anterior=preco_anterior,
                    preco_novo=novo_preco,
                    alterado_por=request.user,
                )
                servico.price = novo_preco

            if preco_promo is not None:
                servico.original_price = preco_promo

            servico.save(update_fields=['price', 'original_price', 'updated_at'])
            return JsonResponse({'ok': True, 'price': str(servico.price)})
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class ServicoToggleAtivoView(View):
    def post(self, request, pk):
        servico = get_object_or_404(Product, pk=pk)
        servico.is_active = not servico.is_active
        servico.save(update_fields=['is_active'])
        return JsonResponse({'ok': True, 'is_active': servico.is_active})


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class RelatorioView(View):
    template_name = 'financeiro/relatorios.html'

    def get(self, request):
        form = RelatorioFilterForm(request.GET or None)
        data_inicio = data_fim = None

        if form.is_valid():
            data_inicio = form.cleaned_data.get('data_inicio')
            data_fim = form.cleaned_data.get('data_fim')

        pedidos, resumo = selectors.get_relatorio(data_inicio, data_fim)
        pedidos = pedidos.select_related('user').order_by('-created_at')

        if request.GET.get('exportar') == 'csv':
            return self._export_csv(pedidos)

        ctx = {
            'title': 'Relatórios Financeiros',
            'form': form,
            'pedidos': pedidos[:200],
            'resumo': resumo,
            'total_pedidos_lista': pedidos.count(),
        }
        return render(request, self.template_name, ctx)

    def _export_csv(self, pedidos):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="relatorio.csv"'
        response.write('\ufeff')  # BOM para Excel reconhecer UTF-8

        writer = csv.writer(response)
        writer.writerow(['ID', 'Cliente', 'E-mail', 'Status', 'Total', 'Data'])
        for p in pedidos:
            writer.writerow([
                str(p.id)[:8].upper(),
                p.customer_name,
                p.customer_email,
                p.get_status_display(),
                str(p.total),
                p.created_at.strftime('%d/%m/%Y %H:%M'),
            ])
        return response


# ═════════════════════════════════════════════════════════════════════════════
# Módulo: Preços por Estado
# URL base: /financeiro/precos/
# ═════════════════════════════════════════════════════════════════════════════

def _registrar_historico_estado(ssp, preco_anterior, novo_preco, user, observacao=''):
    """Registra auditoria de alteração de preço por estado."""
    StatePriceHistory.objects.create(
        service_state_price=ssp,
        service=ssp.service,
        state_code=ssp.state.code,
        preco_anterior=preco_anterior,
        preco_novo=novo_preco,
        alterado_por=user,
        observacao=observacao,
    )


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class PrecosListView(View):
    """Lista paginada de todos os ServiceStatePrice com filtros avançados."""
    template_name = 'financeiro/precos.html'
    paginate_by = 50

    def get(self, request):
        form = PrecoFilterForm(request.GET)
        metricas = selectors.get_metricas_precos()

        q = categoria = servico = estado = ativo = preco_min = preco_max = None
        if form.is_valid():
            q = form.cleaned_data.get('q')
            servico = form.cleaned_data.get('servico')
            categoria = form.cleaned_data.get('categoria')
            estado = form.cleaned_data.get('estado')
            ativo = form.cleaned_data.get('ativo')
            preco_min = form.cleaned_data.get('preco_min')
            preco_max = form.cleaned_data.get('preco_max')

        qs = selectors.get_precos_queryset(
            q=q, servico=servico, categoria=categoria, estado=estado,
            ativo=ativo, preco_min=preco_min, preco_max=preco_max,
        )

        paginator = Paginator(qs, self.paginate_by)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Preserva parâmetros da query para paginação
        query_params = request.GET.copy()
        query_params.pop('page', None)

        ctx = {
            'title': 'Preços por Estado',
            'form': form,
            'page_obj': page_obj,
            'total': paginator.count,
            'metricas': metricas,
            'query_params': query_params.urlencode(),
            'mass_form': MassUpdateForm(),
            'replicate_form': ReplicarPrecosForm(),
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        """Exporta CSV com os filtros atuais."""
        form = PrecoFilterForm(request.GET)
        q = categoria = servico = estado = ativo = preco_min = preco_max = None
        if form.is_valid():
            q = form.cleaned_data.get('q')
            servico = form.cleaned_data.get('servico')
            categoria = form.cleaned_data.get('categoria')
            estado = form.cleaned_data.get('estado')
            ativo = form.cleaned_data.get('ativo')
            preco_min = form.cleaned_data.get('preco_min')
            preco_max = form.cleaned_data.get('preco_max')

        qs = selectors.get_precos_queryset(
            q=q, servico=servico, categoria=categoria, estado=estado,
            ativo=ativo, preco_min=preco_min, preco_max=preco_max,
        )

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="precos_por_estado.csv"'
        response.write('\ufeff')

        writer = csv.writer(response)
        writer.writerow(['Serviço', 'Categoria', 'Estado', 'Preço', 'Promo', 'Ativo', 'Observação', 'Atualizado em'])
        for ssp in qs:
            writer.writerow([
                ssp.service.name,
                ssp.service.category.name,
                ssp.state.code,
                str(ssp.price),
                str(ssp.promotional_price or ''),
                'Sim' if ssp.is_active else 'Não',
                ssp.observacao,
                ssp.updated_at.strftime('%d/%m/%Y %H:%M') if ssp.updated_at else '',
            ])
        return response


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class PrecoCreateView(View):
    """Cria um novo registro de ServiceStatePrice."""
    template_name = 'financeiro/preco_form.html'

    def get(self, request):
        form = ServiceStatePriceForm(initial={
            'service': request.GET.get('service'),
            'state': request.GET.get('state'),
        })
        ctx = {
            'title': 'Novo Preço por Estado',
            'form': form,
            'acao': 'criar',
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        form = ServiceStatePriceForm(request.POST)
        if form.is_valid():
            ssp = form.save()
            _registrar_historico_estado(
                ssp,
                preco_anterior=Decimal('0'),
                novo_preco=ssp.price,
                user=request.user,
                observacao=f'Criação inicial. {ssp.observacao}'.strip(),
            )
            messages.success(
                request,
                f'Preço criado: {ssp.service.name} / {ssp.state.code} → R$ {ssp.price}'
            )
            next_url = request.POST.get('next') or 'financeiro:precos'
            return redirect(next_url)
        ctx = {'title': 'Novo Preço por Estado', 'form': form, 'acao': 'criar'}
        return render(request, self.template_name, ctx)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class PrecoEditView(View):
    """Edita um registro existente de ServiceStatePrice."""
    template_name = 'financeiro/preco_form.html'

    def get(self, request, pk):
        ssp = get_object_or_404(ServiceStatePrice.objects.select_related('service', 'state'), pk=pk)
        form = ServiceStatePriceForm(instance=ssp)
        historico = (
            StatePriceHistory.objects
            .filter(service_state_price=ssp)
            .select_related('alterado_por')[:20]
        )
        ctx = {
            'title': f'Editar: {ssp.service.name} / {ssp.state.code}',
            'form': form,
            'ssp': ssp,
            'historico': historico,
            'acao': 'editar',
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        ssp = get_object_or_404(ServiceStatePrice, pk=pk)
        preco_anterior = ssp.price
        form = ServiceStatePriceForm(request.POST, instance=ssp)
        if form.is_valid():
            ssp_atualizado = form.save()
            if ssp_atualizado.price != preco_anterior:
                _registrar_historico_estado(
                    ssp_atualizado,
                    preco_anterior=preco_anterior,
                    novo_preco=ssp_atualizado.price,
                    user=request.user,
                    observacao=ssp_atualizado.observacao,
                )
            messages.success(
                request,
                f'Preço atualizado: {ssp_atualizado.service.name} / {ssp_atualizado.state.code}'
            )
            return redirect('financeiro:precos')
        historico = (
            StatePriceHistory.objects
            .filter(service_state_price=ssp)
            .select_related('alterado_por')[:20]
        )
        ctx = {
            'title': f'Editar: {ssp.service.name} / {ssp.state.code}',
            'form': form,
            'ssp': ssp,
            'historico': historico,
            'acao': 'editar',
        }
        return render(request, self.template_name, ctx)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class PrecoDeleteView(View):
    """Remove um registro de ServiceStatePrice."""

    def post(self, request, pk):
        ssp = get_object_or_404(ServiceStatePrice.objects.select_related('service', 'state'), pk=pk)
        desc = f'{ssp.service.name} / {ssp.state.code}'
        ssp.delete()
        messages.success(request, f'Preço removido: {desc}')
        return redirect('financeiro:precos')


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class PrecoToggleView(View):
    """Ativa/desativa um ServiceStatePrice via AJAX — com auditoria."""

    def post(self, request, pk):
        ssp = get_object_or_404(ServiceStatePrice.objects.select_related('service', 'state'), pk=pk)
        ssp.is_active = not ssp.is_active
        ssp.save(update_fields=['is_active'])
        return JsonResponse({
            'ok': True,
            'is_active': ssp.is_active,
            'label': 'Ativo' if ssp.is_active else 'Inativo',
        })


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class PrecoInlineUpdateView(View):
    """Atualização inline de preço por estado via AJAX — com auditoria completa."""

    def post(self, request, pk):
        ssp = get_object_or_404(ServiceStatePrice.objects.select_related('service', 'state'), pk=pk)
        try:
            raw = request.POST.get('price', '').strip().replace(',', '.')
            novo_preco = Decimal(raw).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if novo_preco <= 0:
                return JsonResponse({'ok': False, 'error': 'Preço deve ser maior que zero.'}, status=400)
        except (InvalidOperation, ValueError):
            return JsonResponse({'ok': False, 'error': 'Preço inválido.'}, status=400)

        preco_anterior = ssp.price
        if novo_preco != preco_anterior:
            _registrar_historico_estado(
                ssp,
                preco_anterior=preco_anterior,
                novo_preco=novo_preco,
                user=request.user,
                observacao='Edição rápida inline.',
            )
            ssp.price = novo_preco
            ssp.save(update_fields=['price'])

        return JsonResponse({
            'ok': True,
            'price': str(ssp.price),
            'price_fmt': f'R$ {ssp.price:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
        })


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class PrecosMassUpdateView(View):
    """
    Reajuste em massa: percentual, valor fixo ou definir valor exato.
    Aplica a todos os registros que passem pelos filtros selecionados.
    """

    def post(self, request):
        form = MassUpdateForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Formulário inválido. Verifique os campos.')
            return redirect('financeiro:precos')

        tipo = form.cleaned_data['tipo']
        valor = form.cleaned_data['valor']
        categoria = form.cleaned_data.get('categoria')
        estado = form.cleaned_data.get('estado')
        apenas_ativos = form.cleaned_data.get('apenas_ativos', True)
        observacao = form.cleaned_data.get('observacao', '') or 'Reajuste em massa.'

        qs = ServiceStatePrice.objects.select_related('service', 'state')
        if apenas_ativos:
            qs = qs.filter(is_active=True)
        if categoria:
            qs = qs.filter(service__category=categoria)
        if estado:
            qs = qs.filter(state__code=estado.upper())

        atualizados = 0
        erros = 0
        historicos = []

        for ssp in qs.iterator():
            preco_anterior = ssp.price
            try:
                if tipo == 'percentual':
                    novo = (preco_anterior * (1 + valor / 100)).quantize(
                        Decimal('0.01'), rounding=ROUND_HALF_UP
                    )
                elif tipo == 'fixo_adicionar':
                    novo = (preco_anterior + valor).quantize(
                        Decimal('0.01'), rounding=ROUND_HALF_UP
                    )
                elif tipo == 'fixo_subtrair':
                    novo = (preco_anterior - valor).quantize(
                        Decimal('0.01'), rounding=ROUND_HALF_UP
                    )
                elif tipo == 'definir':
                    novo = valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    continue

                if novo <= 0:
                    erros += 1
                    continue

                ssp.price = novo
                ssp.save(update_fields=['price'])

                historicos.append(StatePriceHistory(
                    service_state_price=ssp,
                    service=ssp.service,
                    state_code=ssp.state.code,
                    preco_anterior=preco_anterior,
                    preco_novo=novo,
                    alterado_por=request.user,
                    observacao=observacao,
                ))
                atualizados += 1

            except (InvalidOperation, Exception):
                erros += 1

        if historicos:
            StatePriceHistory.objects.bulk_create(historicos, batch_size=200)

        if atualizados:
            messages.success(request, f'{atualizados} preço(s) atualizados com sucesso.')
        if erros:
            messages.warning(request, f'{erros} registro(s) ignorados (preço resultante ≤ 0 ou erro).')

        return redirect('financeiro:precos')


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class PrecosReplicarView(View):
    """
    Replica o preço de um par (serviço, estado) para outros estados do mesmo serviço,
    ou de um serviço para outro.
    """

    def post(self, request):
        form = ReplicarPrecosForm(request.POST)
        if not form.is_valid():
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f'{field}: {err}')
            return redirect('financeiro:precos')

        servico_origem = form.cleaned_data['servico_origem']
        estado_origem = form.cleaned_data['estado_origem']
        servico_destino = form.cleaned_data.get('servico_destino') or servico_origem
        estados_destino = form.cleaned_data['estados_destino']
        sobrescrever = form.cleaned_data.get('sobrescrever', False)

        # Busca o preço de origem
        try:
            ssp_origem = ServiceStatePrice.objects.select_related('state').get(
                service=servico_origem,
                state__code=estado_origem,
            )
        except ServiceStatePrice.DoesNotExist:
            messages.error(
                request,
                f'Preço de origem não encontrado: {servico_origem.name} / {estado_origem}.'
            )
            return redirect('financeiro:precos')

        preco_ref = ssp_origem.price
        criados = atualizados = ignorados = 0
        historicos = []

        for code in estados_destino:
            if code == estado_origem and servico_destino == servico_origem:
                continue  # pula origem
            try:
                state_obj = State.objects.get(code=code)
            except State.DoesNotExist:
                ignorados += 1
                continue

            ssp, created = ServiceStatePrice.objects.get_or_create(
                service=servico_destino,
                state=state_obj,
                defaults={'price': preco_ref},
            )
            if created:
                historicos.append(StatePriceHistory(
                    service_state_price=ssp,
                    service=servico_destino,
                    state_code=code,
                    preco_anterior=Decimal('0'),
                    preco_novo=preco_ref,
                    alterado_por=request.user,
                    observacao=f'Replicado de {servico_origem.name}/{estado_origem}.',
                ))
                criados += 1
            elif sobrescrever and ssp.price != preco_ref:
                preco_ant = ssp.price
                ssp.price = preco_ref
                ssp.save(update_fields=['price'])
                historicos.append(StatePriceHistory(
                    service_state_price=ssp,
                    service=servico_destino,
                    state_code=code,
                    preco_anterior=preco_ant,
                    preco_novo=preco_ref,
                    alterado_por=request.user,
                    observacao=f'Replicado (sobrescrito) de {servico_origem.name}/{estado_origem}.',
                ))
                atualizados += 1
            else:
                ignorados += 1

        if historicos:
            StatePriceHistory.objects.bulk_create(historicos, batch_size=200)

        msgs = []
        if criados:
            msgs.append(f'{criados} criado(s)')
        if atualizados:
            msgs.append(f'{atualizados} atualizado(s)')
        if ignorados:
            msgs.append(f'{ignorados} ignorado(s)')

        if criados or atualizados:
            messages.success(request, f'Replicação concluída: {", ".join(msgs)}.')
        else:
            messages.info(request, 'Nenhum preço foi alterado. Use "Sobrescrever" para forçar.')

        return redirect('financeiro:precos')


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class PrecosServicoView(View):
    """
    Exibe todos os preços por estado de um serviço específico —
    acessível também pela aba de Serviços.
    """
    template_name = 'financeiro/precos_servico.html'

    def get(self, request, pk):
        servico = get_object_or_404(Product.objects.select_related('category'), pk=pk)
        precos = (
            ServiceStatePrice.objects
            .filter(service=servico)
            .select_related('state')
            .order_by('state__name')
        )
        estados_com_preco = {ssp.state.code for ssp in precos}
        estados_sem_preco = [
            (code, name)
            for code, name in ESTADOS_BR
            if code not in estados_com_preco
        ]
        historico = (
            StatePriceHistory.objects
            .filter(service=servico)
            .select_related('alterado_por')[:30]
        )
        ctx = {
            'title': f'Preços: {servico.name}',
            'servico': servico,
            'precos': precos,
            'estados_sem_preco': estados_sem_preco,
            'historico': historico,
            'estados': ESTADOS_BR,
            'form': ServiceStatePriceForm(initial={'service': servico}),
        }
        return render(request, self.template_name, ctx)



# ═════════════════════════════════════════════════════════════════════════════
# Módulo: Plano de Contas
# URL base: /financeiro/plano-contas/
# ═════════════════════════════════════════════════════════════════════════════

@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class PlanoContasView(View):
    """Árvore do plano de contas com totais do ano por conta."""
    template_name = 'financeiro/plano_contas.html'

    def get(self, request):
        tipo = request.GET.get('tipo', '')
        contas = selectors.get_arvore_plano_contas(tipo=tipo or None)
        total_receitas = sum((c.total_ano for c in contas if c.tipo == 'receita' and c.nivel_cache == 0), Decimal('0'))
        total_despesas = sum((c.total_ano for c in contas if c.tipo == 'despesa' and c.nivel_cache == 0), Decimal('0'))
        ctx = {
            'title': 'Plano de Contas',
            'contas': contas,
            'tipo_filtro': tipo,
            'total_receitas': total_receitas,
            'total_despesas': total_despesas,
            'total_contas': len(contas),
        }
        return render(request, self.template_name, ctx)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class ContaCreateView(View):
    template_name = 'financeiro/conta_form.html'

    def get(self, request):
        form = ContaContabilForm(initial={
            'tipo': request.GET.get('tipo', ''),
            'parent': request.GET.get('parent', ''),
        })
        ctx = {'title': 'Nova Conta Contábil', 'form': form, 'acao': 'criar'}
        return render(request, self.template_name, ctx)

    def post(self, request):
        form = ContaContabilForm(request.POST)
        if form.is_valid():
            conta = form.save()
            messages.success(request, f'Conta "{conta.codigo} — {conta.nome}" criada.')
            return redirect('financeiro:plano_contas')
        ctx = {'title': 'Nova Conta Contábil', 'form': form, 'acao': 'criar'}
        return render(request, self.template_name, ctx)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class ContaEditView(View):
    template_name = 'financeiro/conta_form.html'

    def get(self, request, pk):
        conta = get_object_or_404(ContaContabil, pk=pk)
        form = ContaContabilForm(instance=conta)
        ctx = {
            'title': f'Editar: {conta.codigo} — {conta.nome}',
            'form': form, 'conta': conta, 'acao': 'editar',
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        conta = get_object_or_404(ContaContabil, pk=pk)
        form = ContaContabilForm(request.POST, instance=conta)
        if form.is_valid():
            conta = form.save()
            messages.success(request, f'Conta "{conta.codigo} — {conta.nome}" atualizada.')
            return redirect('financeiro:plano_contas')
        ctx = {
            'title': f'Editar: {conta.codigo} — {conta.nome}',
            'form': form, 'conta': conta, 'acao': 'editar',
        }
        return render(request, self.template_name, ctx)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class ContaDeleteView(View):
    def post(self, request, pk):
        conta = get_object_or_404(ContaContabil, pk=pk)
        if conta.is_system:
            messages.error(request, f'A conta "{conta.nome}" é do sistema e não pode ser excluída. Você pode desativá-la.')
            return redirect('financeiro:plano_contas')
        if conta.filhas.exists():
            messages.error(request, f'A conta "{conta.nome}" possui subcontas. Remova ou mova as subcontas primeiro.')
            return redirect('financeiro:plano_contas')
        if conta.lancamentos.exists():
            messages.error(request, f'A conta "{conta.nome}" possui lançamentos e não pode ser excluída. Desative-a.')
            return redirect('financeiro:plano_contas')
        if conta.servicos_vinculados.exists():
            messages.error(request, f'A conta "{conta.nome}" está vinculada a serviços. Remova os vínculos primeiro.')
            return redirect('financeiro:plano_contas')
        nome = f'{conta.codigo} — {conta.nome}'
        conta.delete()
        messages.success(request, f'Conta "{nome}" excluída.')
        return redirect('financeiro:plano_contas')


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class ContaToggleView(View):
    def post(self, request, pk):
        conta = get_object_or_404(ContaContabil, pk=pk)
        conta.is_active = not conta.is_active
        conta.save(update_fields=['is_active', 'updated_at'])
        return JsonResponse({'ok': True, 'is_active': conta.is_active})


# ═════════════════════════════════════════════════════════════════════════════
# Módulo: Lançamentos (Receitas e Despesas)
# URL base: /financeiro/lancamentos/ | /receitas/ | /despesas/
# ═════════════════════════════════════════════════════════════════════════════

@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class LancamentoListView(View):
    """Listagem de lançamentos. `tipo_fixo` restringe a receitas ou despesas."""
    template_name = 'financeiro/lancamentos.html'
    tipo_fixo = None
    paginate_by = 40

    def get(self, request):
        form = LancamentoFilterForm(request.GET)
        filtros = {}
        if form.is_valid():
            filtros = {
                'q': form.cleaned_data.get('q'),
                'tipo': form.cleaned_data.get('tipo'),
                'conta': form.cleaned_data.get('conta'),
                'status': form.cleaned_data.get('status'),
                'origem': form.cleaned_data.get('origem'),
                'data_inicio': form.cleaned_data.get('data_inicio'),
                'data_fim': form.cleaned_data.get('data_fim'),
            }
        if self.tipo_fixo:
            filtros['tipo'] = self.tipo_fixo

        qs = selectors.get_lancamentos_queryset(**filtros)
        resumo = selectors.get_resumo_lancamentos(qs)

        if request.GET.get('exportar') == 'csv':
            return self._export_csv(qs)

        paginator = Paginator(qs, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        query_params = request.GET.copy()
        query_params.pop('page', None)

        titulos = {'receita': 'Receitas', 'despesa': 'Despesas'}
        ctx = {
            'title': titulos.get(self.tipo_fixo, 'Lançamentos'),
            'tipo_fixo': self.tipo_fixo,
            'form': form,
            'page_obj': page_obj,
            'total': paginator.count,
            'resumo': resumo,
            'query_params': query_params.urlencode(),
        }
        return render(request, self.template_name, ctx)

    def _export_csv(self, qs):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="lancamentos.csv"'
        response.write('﻿')  # BOM para Excel reconhecer UTF-8

        writer = csv.writer(response)
        writer.writerow(['Data', 'Tipo', 'Conta', 'Descrição', 'Valor', 'Status',
                         'Forma Pgto', 'Origem', 'Pedido', 'Observações'])
        for lanc in qs.iterator():
            writer.writerow([
                lanc.data_competencia.strftime('%d/%m/%Y'),
                lanc.get_tipo_display(),
                f'{lanc.conta.codigo} — {lanc.conta.nome}',
                lanc.descricao,
                str(lanc.valor),
                lanc.get_status_display(),
                lanc.get_forma_pagamento_display(),
                lanc.get_origem_display(),
                lanc.order.short_id if lanc.order else '',
                lanc.observacoes,
            ])
        return response


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class LancamentoCreateView(View):
    template_name = 'financeiro/lancamento_form.html'

    def _tipo_fixo(self, request):
        tipo = request.GET.get('tipo') or request.POST.get('tipo_fixo') or ''
        return tipo if tipo in ('receita', 'despesa') else None

    def get(self, request):
        tipo_fixo = self._tipo_fixo(request)
        form = LancamentoForm(tipo_fixo=tipo_fixo, initial={'data_competencia': timezone.localdate()})
        titulos = {'receita': 'Nova Receita', 'despesa': 'Nova Despesa'}
        ctx = {
            'title': titulos.get(tipo_fixo, 'Novo Lançamento'),
            'form': form, 'acao': 'criar', 'tipo_fixo': tipo_fixo,
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        tipo_fixo = self._tipo_fixo(request)
        form = LancamentoForm(request.POST, tipo_fixo=tipo_fixo)
        if form.is_valid():
            lancamento = form.save(commit=False)
            lancamento.origem = 'manual'
            lancamento.criado_por = request.user
            lancamento.save()
            messages.success(request, f'{lancamento.get_tipo_display()} de R$ {lancamento.valor} registrada.')
            if lancamento.tipo == 'receita':
                return redirect('financeiro:receitas')
            return redirect('financeiro:despesas')
        titulos = {'receita': 'Nova Receita', 'despesa': 'Nova Despesa'}
        ctx = {
            'title': titulos.get(tipo_fixo, 'Novo Lançamento'),
            'form': form, 'acao': 'criar', 'tipo_fixo': tipo_fixo,
        }
        return render(request, self.template_name, ctx)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class LancamentoEditView(View):
    template_name = 'financeiro/lancamento_form.html'

    def get(self, request, pk):
        lancamento = get_object_or_404(Lancamento.objects.select_related('conta', 'order'), pk=pk)
        form = LancamentoForm(instance=lancamento)
        ctx = {
            'title': f'Editar Lançamento #{lancamento.pk}',
            'form': form, 'lancamento': lancamento, 'acao': 'editar',
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        lancamento = get_object_or_404(Lancamento, pk=pk)
        form = LancamentoForm(request.POST, instance=lancamento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lançamento atualizado.')
            return redirect('financeiro:lancamentos')
        ctx = {
            'title': f'Editar Lançamento #{lancamento.pk}',
            'form': form, 'lancamento': lancamento, 'acao': 'editar',
        }
        return render(request, self.template_name, ctx)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class LancamentoDeleteView(View):
    def post(self, request, pk):
        lancamento = get_object_or_404(Lancamento, pk=pk)
        desc = f'{lancamento.get_tipo_display()} R$ {lancamento.valor} — {lancamento.descricao}'
        lancamento.delete()
        messages.success(request, f'Lançamento excluído: {desc}')
        next_url = request.POST.get('next') or 'financeiro:lancamentos'
        return redirect(next_url)


@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class LancamentoStatusView(View):
    """Alterna status do lançamento via AJAX (pendente/confirmado/cancelado)."""

    def post(self, request, pk):
        lancamento = get_object_or_404(Lancamento, pk=pk)
        novo_status = request.POST.get('status', '')
        if novo_status not in dict(Lancamento.STATUS_CHOICES):
            return JsonResponse({'ok': False, 'error': 'Status inválido.'}, status=400)
        lancamento.status = novo_status
        if novo_status == 'confirmado' and not lancamento.data_pagamento:
            lancamento.data_pagamento = timezone.localdate()
        lancamento.save(update_fields=['status', 'data_pagamento', 'updated_at'])
        return JsonResponse({'ok': True, 'status': lancamento.status,
                             'label': lancamento.get_status_display()})


# ═════════════════════════════════════════════════════════════════════════════
# Módulo: Vínculos Serviço → Conta de Receita
# URL base: /financeiro/vinculos/
# ═════════════════════════════════════════════════════════════════════════════

@method_decorator(permission_required('visualizar_financeiro'), name='dispatch')
class VinculosServicoContaView(View):
    """Lista serviços e suas contas de receita, com edição inline."""
    template_name = 'financeiro/vinculos.html'

    def get(self, request):
        servicos = (
            Product.objects
            .select_related('category', 'conta_receita_vinculo__conta')
            .order_by('category__order', 'order', 'name')
        )
        contas_receita = (
            ContaContabil.objects
            .filter(tipo='receita', natureza='analitica', is_active=True)
            .order_by('codigo')
        )
        vinculados = sum(1 for s in servicos if getattr(s, 'conta_receita_vinculo', None))
        ctx = {
            'title': 'Vínculos Serviço → Conta',
            'servicos': servicos,
            'contas_receita': contas_receita,
            'total_servicos': len(servicos),
            'vinculados': vinculados,
            'sem_vinculo': len(servicos) - vinculados,
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        """Define/atualiza o vínculo de um serviço via POST inline."""
        service_id = request.POST.get('service_id')
        conta_id = request.POST.get('conta_id')
        servico = get_object_or_404(Product, pk=service_id)

        if not conta_id:
            ServicoContaReceita.objects.filter(service=servico).delete()
            messages.success(request, f'Vínculo removido: {servico.name}.')
            return redirect('financeiro:vinculos')

        conta = get_object_or_404(
            ContaContabil, pk=conta_id, tipo='receita', natureza='analitica',
        )
        ServicoContaReceita.objects.update_or_create(
            service=servico, defaults={'conta': conta},
        )
        messages.success(request, f'Vínculo atualizado: {servico.name} → {conta.codigo} {conta.nome}.')
        return redirect('financeiro:vinculos')
