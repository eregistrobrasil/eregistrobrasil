from django.db import models
from django.contrib.auth.models import User


ACAO_CHOICES = [
    # Navegação
    ('pagina_acessada', 'Página Acessada'),
    # Auth
    ('login', 'Login'),
    ('logout', 'Logout'),
    ('falha_login', 'Falha no Login'),
    ('alteracao_senha', 'Alteração de Senha'),
    # CRUD genérico
    ('criacao', 'Criação'),
    ('edicao', 'Edição'),
    ('exclusao', 'Exclusão'),
    ('visualizacao', 'Visualização'),
    # Arquivos
    ('upload', 'Upload'),
    ('download', 'Download'),
    ('exportacao', 'Exportação'),
    ('importacao', 'Importação'),
    # Segurança
    ('alteracao_permissao', 'Alteração de Permissão'),
    # Sistema
    ('outro', 'Outro'),
]

MODULO_CHOICES = [
    ('auth', 'Autenticação'),
    ('pedidos', 'Pedidos'),
    ('clientes', 'Clientes'),
    ('financeiro', 'Financeiro'),
    ('documentos', 'Documentos'),
    ('usuarios', 'Usuários'),
    ('relatorios', 'Relatórios'),
    ('blog', 'Blog'),
    ('cartorios', 'Cartórios'),
    ('permissoes', 'Permissões'),
    ('sistema', 'Sistema'),
]

STATUS_CHOICES = [
    ('sucesso', 'Sucesso'),
    ('erro', 'Erro'),
    ('negado', 'Acesso Negado'),
    ('redirecionado', 'Redirecionado'),
]


class UserActivity(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atividades',
        verbose_name='Usuário',
    )
    data_hora = models.DateTimeField('Data/Hora', auto_now_add=True, db_index=True)
    modulo = models.CharField('Módulo', max_length=30, choices=MODULO_CHOICES, default='sistema')
    acao = models.CharField('Ação', max_length=30, choices=ACAO_CHOICES, default='pagina_acessada')
    descricao = models.TextField('Descrição', blank=True)
    ip = models.GenericIPAddressField('IP', null=True, blank=True)
    navegador = models.CharField('Navegador/User-Agent', max_length=300, blank=True)
    url = models.CharField('URL', max_length=500, blank=True)
    metodo_http = models.CharField('Método HTTP', max_length=10, blank=True)
    tempo_execucao = models.FloatField('Tempo de Execução (ms)', null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='sucesso')
    objeto_afetado = models.CharField('Objeto Afetado', max_length=100, blank=True)
    id_objeto = models.CharField('ID do Objeto', max_length=100, blank=True)
    dados_anteriores = models.JSONField('Dados Anteriores', null=True, blank=True)
    dados_novos = models.JSONField('Dados Novos', null=True, blank=True)
    observacoes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Atividade do Usuário'
        verbose_name_plural = 'Atividades dos Usuários'
        ordering = ['-data_hora']

    def __str__(self):
        nome = self.usuario.get_full_name() if self.usuario else 'Anônimo'
        return f'[{self.data_hora:%d/%m/%Y %H:%M}] {nome} — {self.get_acao_display()}'

    @property
    def status_color(self):
        return {
            'sucesso': 'green',
            'erro': 'red',
            'negado': 'orange',
            'redirecionado': 'blue',
        }.get(self.status, 'gray')
