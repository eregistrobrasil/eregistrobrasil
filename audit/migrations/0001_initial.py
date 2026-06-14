from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_hora', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Data/Hora')),
                ('modulo', models.CharField(
                    choices=[
                        ('auth', 'Autenticação'), ('pedidos', 'Pedidos'), ('clientes', 'Clientes'),
                        ('financeiro', 'Financeiro'), ('documentos', 'Documentos'), ('usuarios', 'Usuários'),
                        ('relatorios', 'Relatórios'), ('blog', 'Blog'), ('cartorios', 'Cartórios'),
                        ('permissoes', 'Permissões'), ('sistema', 'Sistema'),
                    ],
                    default='sistema', max_length=30, verbose_name='Módulo',
                )),
                ('acao', models.CharField(
                    choices=[
                        ('pagina_acessada', 'Página Acessada'), ('login', 'Login'), ('logout', 'Logout'),
                        ('falha_login', 'Falha no Login'), ('alteracao_senha', 'Alteração de Senha'),
                        ('criacao', 'Criação'), ('edicao', 'Edição'), ('exclusao', 'Exclusão'),
                        ('visualizacao', 'Visualização'), ('upload', 'Upload'), ('download', 'Download'),
                        ('exportacao', 'Exportação'), ('importacao', 'Importação'),
                        ('alteracao_permissao', 'Alteração de Permissão'), ('outro', 'Outro'),
                    ],
                    default='pagina_acessada', max_length=30, verbose_name='Ação',
                )),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição')),
                ('ip', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP')),
                ('navegador', models.CharField(blank=True, max_length=300, verbose_name='Navegador/User-Agent')),
                ('url', models.CharField(blank=True, max_length=500, verbose_name='URL')),
                ('metodo_http', models.CharField(blank=True, max_length=10, verbose_name='Método HTTP')),
                ('tempo_execucao', models.FloatField(blank=True, null=True, verbose_name='Tempo de Execução (ms)')),
                ('status', models.CharField(
                    choices=[
                        ('sucesso', 'Sucesso'), ('erro', 'Erro'),
                        ('negado', 'Acesso Negado'), ('redirecionado', 'Redirecionado'),
                    ],
                    default='sucesso', max_length=20, verbose_name='Status',
                )),
                ('objeto_afetado', models.CharField(blank=True, max_length=100, verbose_name='Objeto Afetado')),
                ('id_objeto', models.CharField(blank=True, max_length=100, verbose_name='ID do Objeto')),
                ('dados_anteriores', models.JSONField(blank=True, null=True, verbose_name='Dados Anteriores')),
                ('dados_novos', models.JSONField(blank=True, null=True, verbose_name='Dados Novos')),
                ('observacoes', models.TextField(blank=True, verbose_name='Observações')),
                ('usuario', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='atividades',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuário',
                )),
            ],
            options={
                'verbose_name': 'Atividade do Usuário',
                'verbose_name_plural': 'Atividades dos Usuários',
                'ordering': ['-data_hora'],
            },
        ),
    ]
