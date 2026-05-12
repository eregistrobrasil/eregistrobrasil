from django.db import models
from django.contrib.auth.models import User
from products.models import Product, ServiceStatePrice


class PriceHistory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='price_history', verbose_name='Serviço'
    )
    preco_anterior = models.DecimalField('Preço Anterior', max_digits=10, decimal_places=2)
    preco_novo = models.DecimalField('Preço Novo', max_digits=10, decimal_places=2)
    alterado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        verbose_name='Alterado por'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Preço'
        verbose_name_plural = 'Histórico de Preços'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.name}: R$ {self.preco_anterior} → R$ {self.preco_novo}'


class StatePriceHistory(models.Model):
    """Auditoria completa de alterações de preço por estado."""
    service_state_price = models.ForeignKey(
        ServiceStatePrice, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='history', verbose_name='Registro de Preço'
    )
    service = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='state_price_history', verbose_name='Serviço'
    )
    state_code = models.CharField('Estado (sigla)', max_length=2, db_index=True)
    preco_anterior = models.DecimalField('Preço Anterior', max_digits=10, decimal_places=2)
    preco_novo = models.DecimalField('Preço Novo', max_digits=10, decimal_places=2)
    alterado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        verbose_name='Alterado por'
    )
    observacao = models.TextField('Observação', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Preço por Estado'
        verbose_name_plural = 'Histórico de Preços por Estado'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['service', 'state_code']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'{self.service.name} / {self.state_code}: R$ {self.preco_anterior} → R$ {self.preco_novo}'
