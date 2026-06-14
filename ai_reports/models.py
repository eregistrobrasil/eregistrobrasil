from django.db import models
from django.contrib.auth.models import User


class DailyUserReport(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='relatorios_diarios',
        verbose_name='Usuário',
    )
    data = models.DateField('Data do Relatório', db_index=True)
    resumo = models.TextField('Resumo Executivo', blank=True)
    indicadores = models.JSONField('Indicadores', default=dict)
    recomendacoes = models.JSONField('Recomendações', default=list)
    alertas = models.JSONField('Alertas / Anomalias', default=list)
    score_produtividade = models.FloatField('Score de Produtividade (0-100)', default=0.0)
    total_acoes = models.IntegerField('Total de Ações', default=0)
    modulos_acessados = models.JSONField('Módulos Acessados', default=list)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Relatório Diário IA'
        verbose_name_plural = 'Relatórios Diários IA'
        unique_together = ('usuario', 'data')
        ordering = ['-data', 'usuario']

    def __str__(self):
        nome = self.usuario.get_full_name() or self.usuario.username
        return f'Relatório {self.data:%d/%m/%Y} — {nome}'

    @property
    def score_color(self):
        if self.score_produtividade >= 75:
            return 'green'
        if self.score_produtividade >= 50:
            return 'yellow'
        return 'red'
