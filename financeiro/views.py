import csv
import json
from decimal import Decimal

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View

from dashboard.views import staff_required
from financeiro import selectors
from financeiro.forms import ProductForm, PriceUpdateForm, RelatorioFilterForm, ServicoFilterForm
from financeiro.models import PriceHistory
from products.models import Product, Category, State, ServiceStatePrice


@method_decorator(staff_required, name='dispatch')
class FinanceiroDashboardView(View):
    template_name = 'financeiro/dashboard.html'

    def get(self, request):
        metricas = selectors.get_metricas_gerais()
        ultimas_vendas = selectors.get_ultimas_vendas(10)

        faturamento_30d = selectors.get_faturamento_por_periodo(30)
        labels = [str(d['dia']) for d in faturamento_30d]
        valores = [float(d['total']) for d in faturamento_30d]

        ctx = {
            'title': 'Dashboard Financeiro',
            'metricas': metricas,
            'ultimas_vendas': ultimas_vendas,
            'chart_labels': json.dumps(labels),
            'chart_valores': json.dumps(valores),
        }
        return render(request, self.template_name, ctx)


@method_decorator(staff_required, name='dispatch')
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


@method_decorator(staff_required, name='dispatch')
class ServicoCreateView(View):
    template_name = 'financeiro/servico_form.html'

    def get(self, request):
        ctx = {'title': 'Novo Serviço', 'form': ProductForm()}
        return render(request, self.template_name, ctx)

    def post(self, request):
        form = ProductForm(request.POST)
        if form.is_valid():
            servico = form.save()
            messages.success(request, f'Serviço "{servico.name}" criado com sucesso.')
            return redirect('financeiro:servicos')
        ctx = {'title': 'Novo Serviço', 'form': form}
        return render(request, self.template_name, ctx)


@method_decorator(staff_required, name='dispatch')
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


@method_decorator(staff_required, name='dispatch')
class ServicoDeleteView(View):
    def post(self, request, pk):
        servico = get_object_or_404(Product, pk=pk)
        nome = servico.name
        servico.delete()
        messages.success(request, f'Serviço "{nome}" excluído.')
        return redirect('financeiro:servicos')


@method_decorator(staff_required, name='dispatch')
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


@method_decorator(staff_required, name='dispatch')
class StatePriceToggleView(View):
    def post(self, request, pk):
        ssp = get_object_or_404(ServiceStatePrice, pk=pk)
        ssp.is_active = not ssp.is_active
        ssp.save(update_fields=['is_active'])
        return JsonResponse({'ok': True, 'is_active': ssp.is_active})


@method_decorator(staff_required, name='dispatch')
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


@method_decorator(staff_required, name='dispatch')
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


@method_decorator(staff_required, name='dispatch')
class ServicoToggleAtivoView(View):
    def post(self, request, pk):
        servico = get_object_or_404(Product, pk=pk)
        servico.is_active = not servico.is_active
        servico.save(update_fields=['is_active'])
        return JsonResponse({'ok': True, 'is_active': servico.is_active})


@method_decorator(staff_required, name='dispatch')
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
