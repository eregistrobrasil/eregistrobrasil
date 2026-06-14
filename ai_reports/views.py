from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Avg, Count

from .models import DailyUserReport
from accounts.permissions import permission_required


@method_decorator(permission_required('visualizar_relatorios'), name='dispatch')
class RelatoriosDashboardView(View):
    template_name = 'ai_reports/dashboard.html'

    def get(self, request):
        hoje = date.today()
        ontem = hoje - timedelta(days=1)

        # Filtros
        user_id = request.GET.get('usuario')
        periodo = int(request.GET.get('periodo', 7))
        desde = hoje - timedelta(days=periodo)

        qs = DailyUserReport.objects.select_related('usuario').filter(data__gte=desde)
        if user_id:
            qs = qs.filter(usuario_id=user_id)

        relatorios = qs.order_by('-data', '-score_produtividade')

        # Métricas de resumo
        media_score = qs.aggregate(media=Avg('score_produtividade'))['media'] or 0
        top_usuarios = (
            DailyUserReport.objects
            .filter(data__gte=desde)
            .values('usuario__id', 'usuario__first_name', 'usuario__last_name', 'usuario__email')
            .annotate(media_score=Avg('score_produtividade'), total_relatorios=Count('id'))
            .order_by('-media_score')[:5]
        )

        # Relatório mais recente de ontem para alertas
        alertas_recentes = []
        for rel in DailyUserReport.objects.filter(data=ontem):
            for alerta in (rel.alertas or []):
                alertas_recentes.append({
                    'usuario': rel.usuario.get_full_name() or rel.usuario.username,
                    'alerta': alerta,
                    'data': rel.data,
                })

        return render(request, self.template_name, {
            'title': 'Relatórios com IA',
            'relatorios': relatorios[:50],
            'media_score': round(media_score, 1),
            'top_usuarios': top_usuarios,
            'alertas_recentes': alertas_recentes[:10],
            'usuarios': User.objects.filter(is_active=True).order_by('first_name'),
            'filtros': {'usuario': user_id, 'periodo': str(periodo)},
            'total': qs.count(),
        })


@method_decorator(permission_required('visualizar_relatorios'), name='dispatch')
class RelatorioDetalheView(View):
    template_name = 'ai_reports/detalhe.html'

    def get(self, request, pk):
        relatorio = get_object_or_404(DailyUserReport, pk=pk)
        return render(request, self.template_name, {
            'title': str(relatorio),
            'relatorio': relatorio,
        })


@method_decorator(permission_required('visualizar_relatorios'), name='dispatch')
class GerarRelatorioManualView(View):
    """Dispara a geração manual via task Celery para um usuário/data."""

    def post(self, request):
        user_id = request.POST.get('usuario')
        data_iso = request.POST.get('data', date.today().isoformat())

        if not user_id:
            messages.error(request, 'Selecione um usuário.')
            return redirect('ai_reports:dashboard')

        from ai_reports.tasks import gerar_relatorio_usuario_manual
        gerar_relatorio_usuario_manual.delay(int(user_id), data_iso)

        messages.success(request, f'Relatório para {data_iso} enfileirado com sucesso.')
        return redirect('ai_reports:dashboard')
