from .models import Notification


def notifications_processor(request):
    if request.user.is_authenticated:
        nao_lidas_qs = Notification.ativas(request.user).filter(lida=False)
        return {
            'notificacoes_nao_lidas': nao_lidas_qs.count(),
            'notificacoes_recentes': nao_lidas_qs.select_related('order')[:5],
        }
    return {}
