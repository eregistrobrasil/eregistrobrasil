"""
Signals Django para auditoria automática de autenticação e CRUD.
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    try:
        from audit.services.audit_service import registrar_login
        registrar_login(user, request, sucesso=True)
    except Exception:
        pass


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    if user:
        try:
            from audit.services.audit_service import registrar_logout
            registrar_logout(user, request)
        except Exception:
            pass


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request, **kwargs):
    try:
        from audit.tasks import registrar_atividade_async
        email = credentials.get('username', credentials.get('email', '?'))
        registrar_atividade_async.delay(
            user_id=None,
            acao='falha_login',
            modulo='auth',
            descricao=f'Tentativa de login falhou para: {email}',
            ip=request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                or request.META.get('REMOTE_ADDR', ''),
            navegador=request.META.get('HTTP_USER_AGENT', '')[:300],
            url=request.path,
            metodo_http='POST',
            status='erro',
            observacoes=f'Credencial usada: {email}',
        )
    except Exception:
        pass
