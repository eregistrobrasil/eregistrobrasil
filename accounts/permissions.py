"""
Helpers, decorators e mixins para o sistema de permissões customizado.
"""
from functools import wraps

from django.conf import settings
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import render, redirect


def _is_full_access_user(user) -> bool:
    """Superusuários e administradores do sistema têm acesso irrestrito."""
    if user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.tipo == 'admin')


def has_permission(user, codename: str) -> bool:
    """Verifica se o usuário possui a permissão indicada."""
    if not user or not user.is_authenticated:
        return False
    if _is_full_access_user(user):
        return True
    try:
        up = user.permissoes_customizadas
    except Exception:
        return False
    return codename in up.get_all_codenames()


def get_user_permissions(user) -> set:
    """Retorna o conjunto de codenames permitidos para o usuário."""
    if not user or not user.is_authenticated:
        return set()
    if _is_full_access_user(user):
        from accounts.models import CODENAME_CHOICES
        return {code for code, _ in CODENAME_CHOICES}
    try:
        return user.permissoes_customizadas.get_all_codenames()
    except Exception:
        return set()


def is_staff_user(user) -> bool:
    """Verifica se é usuário com acesso ao painel operacional."""
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return (
        hasattr(user, 'profile')
        and user.profile.tipo in ('admin', 'operador', 'financeiro')
    )


# ── Decorators ───────────────────────────────────────────────────────────────

def permission_required(codename: str):
    """Decorator para views baseadas em função."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f'{settings.LOGIN_URL}?next={request.path}')
            if not has_permission(request.user, codename):
                return render(request, '403.html', {'codename': codename}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def staff_required(view_func):
    """Decorator que exige acesso ao painel operacional (permissão acessar_painel_admin)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        # Superusuários e tipo='admin' têm acesso total sem precisar de permissão explícita
        if _is_full_access_user(request.user):
            return view_func(request, *args, **kwargs)
        # Demais usuários de staff precisam da permissão acessar_painel_admin
        if not is_staff_user(request.user) or not has_permission(request.user, 'acessar_painel_admin'):
            return render(request, '403.html', {}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Mixins ───────────────────────────────────────────────────────────────────

class PermissionRequiredMixin(AccessMixin):
    """Mixin para views baseadas em classe. Define `required_permission`."""
    required_permission: str = ''

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not has_permission(request.user, self.required_permission):
            return render(request, '403.html', {'codename': self.required_permission}, status=403)
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin(AccessMixin):
    """Mixin que exige acesso ao painel operacional (permissão acessar_painel_admin)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if _is_full_access_user(request.user):
            return super().dispatch(request, *args, **kwargs)
        if not is_staff_user(request.user) or not has_permission(request.user, 'acessar_painel_admin'):
            return render(request, '403.html', {}, status=403)
        return super().dispatch(request, *args, **kwargs)


class SuperuserRequiredMixin(AccessMixin):
    """Mixin que exige superusuário."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_superuser:
            return render(request, '403.html', {}, status=403)
        return super().dispatch(request, *args, **kwargs)
