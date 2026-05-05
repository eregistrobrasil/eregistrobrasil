from django.db import models
from django.contrib.auth.models import User
from products.models import Product


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
