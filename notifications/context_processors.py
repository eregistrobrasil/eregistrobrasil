from .models import Notification


def notifications_processor(request):
    if request.user.is_authenticated:
        return {
            'notificacoes_nao_lidas': Notification.nao_lidas(request.user),
            'notificacoes_recentes': Notification.objects.filter(
                usuario=request.user, lida=False
            ).select_related('order')[:5],
        }
    return {}
