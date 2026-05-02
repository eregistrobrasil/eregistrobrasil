from django.db import models


class Registry(models.Model):
    nome = models.CharField('Nome', max_length=200)
    estado = models.CharField('Estado (UF)', max_length=2)
    cidade = models.CharField('Cidade', max_length=100)
    contato = models.CharField('Contato', max_length=200, blank=True)
    email = models.EmailField('E-mail', blank=True)
    prazo_medio_dias = models.PositiveIntegerField('Prazo Médio (dias)', default=15)
    observacoes = models.TextField('Observações', blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cartório'
        verbose_name_plural = 'Cartórios'
        ordering = ['estado', 'cidade', 'nome']
        indexes = [models.Index(fields=['estado', 'cidade'])]

    def __str__(self):
        return f'{self.nome} — {self.cidade}/{self.estado}'
