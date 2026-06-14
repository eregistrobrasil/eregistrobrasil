"""
Middleware que captura cada requisição autenticada e envia para registro assíncrono.
Rotas estáticas, de mídia e de health-check são ignoradas.
"""
import time

_EXCLUDED_PREFIXES = (
    '/static/', '/media/', '/favicon.ico',
    '/api/', '/sitemap.xml', '/robots.txt',
    '/admin/jsi18n/',
)

_EXCLUDED_EXTENSIONS = ('.js', '.css', '.png', '.jpg', '.jpeg', '.svg', '.ico', '.woff', '.woff2')

_PATH_TO_MODULO = {
    '/conta/': 'auth',
    '/painel/': 'sistema',
    '/pedidos/': 'pedidos',
    '/pagamentos/': 'financeiro',
    '/financeiro/': 'financeiro',
    '/documentos/': 'documentos',
    '/blog/': 'blog',
    '/relatorios/': 'relatorios',
    '/audit/': 'sistema',
    '/conta/permissoes/': 'permissoes',
}


def _detect_module(path: str) -> str:
    for prefix, modulo in _PATH_TO_MODULO.items():
        if path.startswith(prefix):
            return modulo
    return 'sistema'


def _get_ip(request) -> str:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _should_skip(path: str) -> bool:
    for prefix in _EXCLUDED_PREFIXES:
        if path.startswith(prefix):
            return True
    for ext in _EXCLUDED_EXTENSIONS:
        if path.endswith(ext):
            return True
    return False


class ActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)

        if (
            request.user.is_authenticated
            and not _should_skip(request.path)
            and request.method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')
        ):
            elapsed_ms = (time.monotonic() - start) * 1000
            status_code = response.status_code

            if status_code >= 400:
                log_status = 'negado' if status_code == 403 else 'erro'
            elif status_code in (301, 302):
                log_status = 'redirecionado'
            else:
                log_status = 'sucesso'

            try:
                from audit.tasks import registrar_atividade_async
                registrar_atividade_async.delay(
                    user_id=request.user.id,
                    acao='pagina_acessada',
                    modulo=_detect_module(request.path),
                    descricao='',
                    ip=_get_ip(request),
                    navegador=request.META.get('HTTP_USER_AGENT', '')[:300],
                    url=request.path[:500],
                    metodo_http=request.method,
                    tempo_execucao=round(elapsed_ms, 2),
                    status=log_status,
                )
            except Exception:
                pass

        return response
