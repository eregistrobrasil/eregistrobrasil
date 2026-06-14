"""
Funções de alto nível para registrar eventos de auditoria.
Todas as funções enfileiram via Celery para não bloquear a requisição.
"""
from django.utils import timezone


def _get_ip(request) -> str:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def registrar_evento(
    usuario=None,
    acao: str = 'outro',
    modulo: str = 'sistema',
    descricao: str = '',
    ip: str = '',
    navegador: str = '',
    url: str = '',
    metodo_http: str = '',
    tempo_execucao: float = None,
    status: str = 'sucesso',
    objeto_afetado: str = '',
    id_objeto: str = '',
    dados_anteriores=None,
    dados_novos=None,
    observacoes: str = '',
):
    """Registra um evento de auditoria de forma assíncrona."""
    from audit.tasks import registrar_atividade_async

    user_id = usuario.id if usuario and hasattr(usuario, 'id') else None

    registrar_atividade_async.delay(
        user_id=user_id,
        acao=acao,
        modulo=modulo,
        descricao=descricao,
        ip=ip,
        navegador=navegador,
        url=url,
        metodo_http=metodo_http,
        tempo_execucao=tempo_execucao,
        status=status,
        objeto_afetado=objeto_afetado,
        id_objeto=str(id_objeto) if id_objeto else '',
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        observacoes=observacoes,
    )


def registrar_evento_request(request, acao: str, modulo: str, **kwargs):
    """Atalho que extrai IP e user-agent do request."""
    registrar_evento(
        usuario=request.user if request.user.is_authenticated else None,
        acao=acao,
        modulo=modulo,
        ip=_get_ip(request),
        navegador=request.META.get('HTTP_USER_AGENT', '')[:300],
        url=request.path,
        metodo_http=request.method,
        **kwargs,
    )


def registrar_alteracao(usuario, objeto, dados_anteriores: dict, dados_novos: dict, request=None):
    """Registra uma alteração CRUD com diff de dados."""
    obj_name = type(objeto).__name__
    obj_id = getattr(objeto, 'pk', '') or ''
    kwargs = dict(
        usuario=usuario,
        acao='edicao',
        modulo='sistema',
        descricao=f'Alteração em {obj_name} #{obj_id}',
        objeto_afetado=obj_name,
        id_objeto=str(obj_id),
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
    )
    if request:
        kwargs['ip'] = _get_ip(request)
        kwargs['navegador'] = request.META.get('HTTP_USER_AGENT', '')[:300]
        kwargs['url'] = request.path
        kwargs['metodo_http'] = request.method
    registrar_evento(**kwargs)


def registrar_login(usuario, request, sucesso: bool = True):
    """Registra tentativa de login."""
    registrar_evento(
        usuario=usuario if sucesso else None,
        acao='login' if sucesso else 'falha_login',
        modulo='auth',
        descricao=f'Login {"bem-sucedido" if sucesso else "falhou"} para {getattr(usuario, "email", "?")}',
        ip=_get_ip(request),
        navegador=request.META.get('HTTP_USER_AGENT', '')[:300],
        url=request.path,
        metodo_http='POST',
        status='sucesso' if sucesso else 'erro',
    )


def registrar_logout(usuario, request):
    """Registra logout."""
    registrar_evento(
        usuario=usuario,
        acao='logout',
        modulo='auth',
        descricao=f'Logout de {getattr(usuario, "email", "?")}',
        ip=_get_ip(request),
        navegador=request.META.get('HTTP_USER_AGENT', '')[:300],
        url=request.path,
        metodo_http='POST',
    )
