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
            name='DailyUserReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(db_index=True, verbose_name='Data do Relatório')),
                ('resumo', models.TextField(blank=True, verbose_name='Resumo Executivo')),
                ('indicadores', models.JSONField(default=dict, verbose_name='Indicadores')),
                ('recomendacoes', models.JSONField(default=list, verbose_name='Recomendações')),
                ('alertas', models.JSONField(default=list, verbose_name='Alertas / Anomalias')),
                ('score_produtividade', models.FloatField(default=0.0, verbose_name='Score de Produtividade (0-100)')),
                ('total_acoes', models.IntegerField(default=0, verbose_name='Total de Ações')),
                ('modulos_acessados', models.JSONField(default=list, verbose_name='Módulos Acessados')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='relatorios_diarios',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuário',
                )),
            ],
            options={
                'verbose_name': 'Relatório Diário IA',
                'verbose_name_plural': 'Relatórios Diários IA',
                'ordering': ['-data', 'usuario'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='dailyuserreport',
            unique_together={('usuario', 'data')},
        ),
    ]
