"""
Views para gerenciamento de permissões, roles e criação de usuários no painel.
"""
import secrets
import string

from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View

from .models import Permissao, Role, UserPermission, UserProfile, MODULO_CHOICES
from .permissions import staff_required


def _gerar_senha(tamanho: int = 12) -> str:
    alfabeto = string.ascii_letters + string.digits + '!@#$'
    while True:
        senha = ''.join(secrets.choice(alfabeto) for _ in range(tamanho))
        if (any(c.isupper() for c in senha)
                and any(c.islower() for c in senha)
                and any(c.isdigit() for c in senha)):
            return senha


@method_decorator(staff_required, name='dispatch')
class PermissaoListView(View):
    template_name = 'accounts/permissions/list.html'

    def get(self, request):
        Permissao.popular_permissoes()
        permissoes_por_modulo = {}
        for cod, label in MODULO_CHOICES:
            permissoes_por_modulo[label] = Permissao.objects.filter(modulo=cod)

        roles = Role.objects.prefetch_related('permissoes').all()
        usuarios_com_permissoes = UserPermission.objects.select_related('user').prefetch_related(
            'roles', 'permissoes_extras', 'permissoes_negadas'
        )

        return render(request, self.template_name, {
            'title': 'Controle de Permissões',
            'permissoes_por_modulo': permissoes_por_modulo,
            'roles': roles,
            'usuarios_com_permissoes': usuarios_com_permissoes,
        })


@method_decorator(staff_required, name='dispatch')
class RoleCreateView(View):
    template_name = 'accounts/permissions/role_form.html'

    def get(self, request):
        Permissao.popular_permissoes()
        return render(request, self.template_name, {
            'title': 'Criar Papel (Role)',
            'permissoes': Permissao.objects.all(),
            'modulos': MODULO_CHOICES,
        })

    def post(self, request):
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        permissao_ids = request.POST.getlist('permissoes')

        if not nome:
            messages.error(request, 'O nome é obrigatório.')
            return redirect('accounts:role_create')

        role, _ = Role.objects.get_or_create(nome=nome, defaults={'descricao': descricao})
        role.descricao = descricao
        role.save()
        role.permissoes.set(Permissao.objects.filter(id__in=permissao_ids))
        messages.success(request, f'Papel "{nome}" criado com sucesso.')
        return redirect('accounts:permissions_list')


@method_decorator(staff_required, name='dispatch')
class RoleEditView(View):
    template_name = 'accounts/permissions/role_form.html'

    def get(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        Permissao.popular_permissoes()
        return render(request, self.template_name, {
            'title': f'Editar Papel — {role.nome}',
            'role': role,
            'permissoes': Permissao.objects.all(),
            'modulos': MODULO_CHOICES,
            'selecionadas': set(role.permissoes.values_list('id', flat=True)),
        })

    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        role.nome = request.POST.get('nome', role.nome).strip()
        role.descricao = request.POST.get('descricao', '').strip()
        role.save()
        permissao_ids = request.POST.getlist('permissoes')
        role.permissoes.set(Permissao.objects.filter(id__in=permissao_ids))
        messages.success(request, f'Papel "{role.nome}" atualizado.')
        return redirect('accounts:permissions_list')


@method_decorator(staff_required, name='dispatch')
class RoleDeleteView(View):
    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        nome = role.nome
        role.delete()
        messages.success(request, f'Papel "{nome}" excluído.')
        return redirect('accounts:permissions_list')


@method_decorator(staff_required, name='dispatch')
class UserPermissionView(View):
    """Gerencia permissões de um usuário específico."""
    template_name = 'accounts/permissions/usuario.html'

    def get(self, request, user_id):
        usuario = get_object_or_404(User, pk=user_id)
        Permissao.popular_permissoes()
        up, _ = UserPermission.objects.get_or_create(user=usuario)
        return render(request, self.template_name, {
            'title': f'Permissões — {usuario.get_full_name() or usuario.username}',
            'usuario': usuario,
            'up': up,
            'roles': Role.objects.all(),
            'permissoes': Permissao.objects.all(),
            'modulos': MODULO_CHOICES,
            'roles_selecionados': set(up.roles.values_list('id', flat=True)),
            'extras_selecionadas': set(up.permissoes_extras.values_list('id', flat=True)),
            'negadas_selecionadas': set(up.permissoes_negadas.values_list('id', flat=True)),
        })

    def post(self, request, user_id):
        usuario = get_object_or_404(User, pk=user_id)
        up, _ = UserPermission.objects.get_or_create(user=usuario)

        role_ids = request.POST.getlist('roles')
        extra_ids = request.POST.getlist('permissoes_extras')
        negadas_ids = request.POST.getlist('permissoes_negadas')

        up.roles.set(Role.objects.filter(id__in=role_ids))
        up.permissoes_extras.set(Permissao.objects.filter(id__in=extra_ids))
        up.permissoes_negadas.set(Permissao.objects.filter(id__in=negadas_ids))

        messages.success(request, f'Permissões de {usuario.get_full_name() or usuario.username} atualizadas.')
        return redirect('accounts:permissions_list')


@method_decorator(staff_required, name='dispatch')
class UsersListView(View):
    """Lista todos os usuários para gerenciamento de permissões."""
    template_name = 'accounts/permissions/usuarios_lista.html'

    def get(self, request):
        usuarios = User.objects.select_related('profile').prefetch_related(
            'permissoes_customizadas__roles',
        ).order_by('-date_joined')
        return render(request, self.template_name, {
            'title': 'Usuários do Sistema',
            'usuarios': usuarios,
            'tipo_choices': UserProfile.TIPO_CHOICES,
        })


@method_decorator(staff_required, name='dispatch')
class UserCreateView(View):
    """Cria um novo usuário interno (staff) com tipo e senha gerada."""
    template_name = 'accounts/permissions/usuario_criar.html'

    def get(self, request):
        return render(request, self.template_name, {
            'title': 'Criar Usuário',
            'tipo_choices': UserProfile.TIPO_CHOICES,
        })

    def post(self, request):
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        tipo = request.POST.get('tipo', 'operador')
        cpf = request.POST.get('cpf', '').strip()
        phone = request.POST.get('phone', '').strip()
        is_staff = request.POST.get('is_staff') == '1'
        definir_senha = request.POST.get('definir_senha') == '1'
        senha_manual = request.POST.get('senha', '').strip()

        # Validações básicas
        if not email:
            messages.error(request, 'O e-mail é obrigatório.')
            return redirect('accounts:user_create')

        if User.objects.filter(email=email).exists():
            messages.error(request, f'Já existe um usuário com o e-mail "{email}".')
            return redirect('accounts:user_create')

        if definir_senha and not senha_manual:
            messages.error(request, 'Informe a senha ou desmarque a opção de senha manual.')
            return redirect('accounts:user_create')

        # Criar usuário
        senha = senha_manual if definir_senha else _gerar_senha()
        username = email  # usar e-mail como username

        # Garantir username único
        base = username
        contador = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}_{contador}'
            contador += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=senha,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
        )

        # Atualizar perfil (criado pelo signal)
        profile = user.profile
        profile.tipo = tipo
        profile.cpf = cpf
        profile.phone = phone
        if not definir_senha:
            profile.senha_gerada_automaticamente = True
        profile.save()

        if definir_senha:
            messages.success(
                request,
                f'Usuário "{user.get_full_name() or email}" criado com sucesso.'
            )
        else:
            messages.success(
                request,
                f'Usuário "{user.get_full_name() or email}" criado. '
                f'Senha gerada: {senha}'
            )

        return redirect('accounts:user_permissions', user_id=user.pk)
