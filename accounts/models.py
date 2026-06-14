from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    TIPO_CHOICES = [
        ('admin', 'Administrador'),
        ('operador', 'Operador'),
        ('financeiro', 'Financeiro'),
        ('cliente', 'Cliente'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    tipo = models.CharField('Tipo', max_length=15, choices=TIPO_CHOICES, default='cliente')
    cpf = models.CharField('CPF', max_length=14, blank=True)
    phone = models.CharField('Telefone', max_length=20, blank=True)
    birth_date = models.DateField('Data de Nascimento', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    senha_gerada_automaticamente = models.BooleanField(
        'Senha gerada automaticamente', default=False
    )
    senha_alterada_pelo_usuario = models.BooleanField(
        'Senha alterada pelo usuário', default=False
    )

    class Meta:
        verbose_name = 'Perfil do Usuário'
        verbose_name_plural = 'Perfis dos Usuários'

    def __str__(self):
        return f'Perfil de {self.user.get_full_name() or self.user.username}'

    @property
    def is_operador(self):
        return self.tipo in ('admin', 'operador')

    @property
    def is_financeiro(self):
        return self.tipo in ('admin', 'financeiro')

    @property
    def is_admin(self):
        return self.tipo == 'admin'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


# ── Sistema de Permissões ────────────────────────────────────────────────────

MODULO_CHOICES = [
    ('usuarios', 'Usuários'),
    ('clientes', 'Clientes'),
    ('financeiro', 'Financeiro'),
    ('relatorios', 'Relatórios'),
    ('historico', 'Histórico'),
    ('admin', 'Administração'),
]

CODENAME_CHOICES = [
    # Usuários
    ('visualizar_usuarios', 'Visualizar Usuários'),
    ('criar_usuarios', 'Criar Usuários'),
    ('editar_usuarios', 'Editar Usuários'),
    ('excluir_usuarios', 'Excluir Usuários'),
    # Clientes
    ('visualizar_clientes', 'Visualizar Clientes'),
    ('criar_clientes', 'Criar Clientes'),
    ('editar_clientes', 'Editar Clientes'),
    ('excluir_clientes', 'Excluir Clientes'),
    # Financeiro
    ('visualizar_financeiro', 'Visualizar Financeiro'),
    ('editar_financeiro', 'Editar Financeiro'),
    # Relatórios
    ('visualizar_relatorios', 'Visualizar Relatórios'),
    # Histórico
    ('visualizar_historico', 'Visualizar Histórico'),
    # Admin
    ('acessar_painel_admin', 'Acessar Painel Administrativo'),
]

CODENAME_TO_MODULO = {
    'visualizar_usuarios': 'usuarios',
    'criar_usuarios': 'usuarios',
    'editar_usuarios': 'usuarios',
    'excluir_usuarios': 'usuarios',
    'visualizar_clientes': 'clientes',
    'criar_clientes': 'clientes',
    'editar_clientes': 'clientes',
    'excluir_clientes': 'clientes',
    'visualizar_financeiro': 'financeiro',
    'editar_financeiro': 'financeiro',
    'visualizar_relatorios': 'relatorios',
    'visualizar_historico': 'historico',
    'acessar_painel_admin': 'admin',
}


class Permissao(models.Model):
    codename = models.CharField(
        'Código', max_length=60, unique=True, choices=CODENAME_CHOICES
    )
    nome = models.CharField('Nome', max_length=120)
    modulo = models.CharField('Módulo', max_length=20, choices=MODULO_CHOICES)
    descricao = models.TextField('Descrição', blank=True)

    class Meta:
        verbose_name = 'Permissão'
        verbose_name_plural = 'Permissões'
        ordering = ['modulo', 'codename']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.modulo:
            self.modulo = CODENAME_TO_MODULO.get(self.codename, 'admin')
        super().save(*args, **kwargs)

    @classmethod
    def popular_permissoes(cls):
        """Cria todas as permissões padrão se não existirem."""
        for codename, nome in CODENAME_CHOICES:
            modulo = CODENAME_TO_MODULO.get(codename, 'admin')
            cls.objects.get_or_create(
                codename=codename,
                defaults={'nome': nome, 'modulo': modulo},
            )


class Role(models.Model):
    nome = models.CharField('Nome', max_length=100, unique=True)
    descricao = models.TextField('Descrição', blank=True)
    permissoes = models.ManyToManyField(
        Permissao, blank=True, verbose_name='Permissões', related_name='roles'
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Papel (Role)'
        verbose_name_plural = 'Papéis (Roles)'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class UserPermission(models.Model):
    """Vincula permissões e roles a um usuário individualmente."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='permissoes_customizadas'
    )
    roles = models.ManyToManyField(
        Role, blank=True, verbose_name='Papéis', related_name='usuarios'
    )
    permissoes_extras = models.ManyToManyField(
        Permissao, blank=True,
        verbose_name='Permissões Extras',
        related_name='usuarios_diretos',
    )
    permissoes_negadas = models.ManyToManyField(
        Permissao, blank=True,
        verbose_name='Permissões Negadas',
        related_name='usuarios_negados',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Permissões do Usuário'
        verbose_name_plural = 'Permissões dos Usuários'

    def __str__(self):
        return f'Permissões de {self.user.get_full_name() or self.user.username}'

    def get_all_codenames(self):
        """Retorna o conjunto final de codenames permitidos para este usuário."""
        negadas = set(
            self.permissoes_negadas.values_list('codename', flat=True)
        )
        diretas = set(
            self.permissoes_extras.values_list('codename', flat=True)
        )
        via_roles = set(
            self.roles.values_list('permissoes__codename', flat=True)
        ) - {None}
        return (diretas | via_roles) - negadas
