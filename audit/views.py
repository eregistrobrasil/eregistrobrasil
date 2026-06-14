from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import UserActivity, ACAO_CHOICES, MODULO_CHOICES
from accounts.permissions import permission_required


@method_decorator(permission_required('visualizar_historico'), name='dispatch')
class HistoricoView(View):
    template_name = 'audit/historico.html'

    def get(self, request):
        qs = UserActivity.objects.select_related('usuario').all()

        # Filtros
        usuario_id = request.GET.get('usuario')
        acao = request.GET.get('acao')
        modulo = request.GET.get('modulo')
        periodo = request.GET.get('periodo', '7')
        status = request.GET.get('status')

        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        if acao:
            qs = qs.filter(acao=acao)
        if modulo:
            qs = qs.filter(modulo=modulo)
        if status:
            qs = qs.filter(status=status)

        try:
            dias = int(periodo)
        except (ValueError, TypeError):
            dias = 7
        desde = timezone.now() - timedelta(days=dias)
        qs = qs.filter(data_hora__gte=desde)

        # Paginação simples
        pagina = max(1, int(request.GET.get('pagina', 1)))
        por_pagina = 50
        total = qs.count()
        offset = (pagina - 1) * por_pagina
        atividades = qs[offset: offset + por_pagina]

        total_paginas = (total + por_pagina - 1) // por_pagina

        return render(request, self.template_name, {
            'title': 'Histórico de Atividades',
            'atividades': atividades,
            'usuarios': User.objects.filter(is_active=True).order_by('first_name'),
            'acao_choices': ACAO_CHOICES,
            'modulo_choices': MODULO_CHOICES,
            'filtros': {
                'usuario': usuario_id,
                'acao': acao,
                'modulo': modulo,
                'periodo': periodo,
                'status': status,
            },
            'total': total,
            'pagina': pagina,
            'total_paginas': total_paginas,
        })


@method_decorator(permission_required('visualizar_historico'), name='dispatch')
class AtividadeDetalheView(View):
    template_name = 'audit/detalhe.html'

    def get(self, request, pk):
        atividade = get_object_or_404(UserActivity, pk=pk)
        return render(request, self.template_name, {
            'title': f'Atividade #{pk}',
            'atividade': atividade,
        })
