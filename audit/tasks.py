from celery import shared_task


@shared_task(name='audit.registrar_atividade', ignore_result=True)
def registrar_atividade_async(
    user_id=None,
    acao='pagina_acessada',
    modulo='sistema',
    descricao='',
    ip='',
    navegador='',
    url='',
    metodo_http='',
    tempo_execucao=None,
    status='sucesso',
    objeto_afetado='',
    id_objeto='',
    dados_anteriores=None,
    dados_novos=None,
    observacoes='',
):
    """Persiste um registro de atividade no banco de dados de forma assíncrona."""
    from django.contrib.auth.models import User
    from audit.models import UserActivity

    usuario = None
    if user_id:
        try:
            usuario = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            pass

    UserActivity.objects.create(
        usuario=usuario,
        acao=acao,
        modulo=modulo,
        descricao=descricao,
        ip=ip or None,
        navegador=navegador[:300],
        url=url[:500],
        metodo_http=metodo_http[:10],
        tempo_execucao=tempo_execucao,
        status=status,
        objeto_afetado=objeto_afetado[:100],
        id_objeto=id_objeto[:100],
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        observacoes=observacoes,
    )


@shared_task(name='audit.limpar_logs_antigos', ignore_result=True)
def limpar_logs_antigos():
    """Remove atividades mais antigas que AUDIT_LOG_RETENTION_DAYS."""
    from django.conf import settings
    from django.utils import timezone
    from datetime import timedelta
    from audit.models import UserActivity

    dias = getattr(settings, 'AUDIT_LOG_RETENTION_DAYS', 90)
    limite = timezone.now() - timedelta(days=dias)
    deletados, _ = UserActivity.objects.filter(data_hora__lt=limite).delete()
    return f'Removidos {deletados} registros anteriores a {limite:%d/%m/%Y}'
