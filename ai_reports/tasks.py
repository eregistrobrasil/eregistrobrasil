import logging
from datetime import date, timedelta

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='ai_reports.gerar_relatorio_diario', ignore_result=True)
def gerar_relatorio_diario():
    """
    Executada às 01:00 diariamente.
    Gera relatórios de IA para todos os usuários ativos do dia anterior.
    """
    from django.contrib.auth.models import User
    from audit.models import UserActivity
    from ai_reports.services.ai_service import gerar_relatorio_usuario

    ontem = date.today() - timedelta(days=1)

    user_ids = (
        UserActivity.objects
        .filter(data_hora__date=ontem, usuario__isnull=False)
        .values_list('usuario_id', flat=True)
        .distinct()
    )

    usuarios = User.objects.filter(id__in=user_ids)
    total = 0

    for usuario in usuarios:
        try:
            gerar_relatorio_usuario(usuario, ontem)
            total += 1
        except Exception as exc:
            logger.exception(
                'Erro ao gerar relatório para %s em %s: %s',
                usuario.email, ontem, exc,
            )

    logger.info('Relatórios diários gerados: %d usuários para %s', total, ontem)
    return f'{total} relatórios gerados para {ontem}'


@shared_task(name='ai_reports.gerar_relatorio_usuario_manual', ignore_result=True)
def gerar_relatorio_usuario_manual(user_id: int, data_iso: str):
    """Gera o relatório de um usuário específico para uma data (YYYY-MM-DD)."""
    from django.contrib.auth.models import User
    from ai_reports.services.ai_service import gerar_relatorio_usuario

    try:
        usuario = User.objects.get(pk=user_id)
        data_ref = date.fromisoformat(data_iso)
        gerar_relatorio_usuario(usuario, data_ref)
    except User.DoesNotExist:
        logger.error('Usuário %d não encontrado', user_id)
    except Exception as exc:
        logger.exception('Erro ao gerar relatório manual: %s', exc)
