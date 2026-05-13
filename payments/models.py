from django.db import models
from orders.models import Order


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('authorized', 'Autorizado'),
        ('in_process', 'Em Processamento'),
        ('in_mediation', 'Em Mediação'),
        ('rejected', 'Rejeitado'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
        ('charged_back', 'Estornado'),
    ]

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='payment'
    )
    mercadopago_id = models.CharField('ID MP', max_length=200, blank=True)
    preference_id = models.CharField('Preference ID', max_length=200, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    status_detail = models.CharField('Detalhe do Status', max_length=200, blank=True)
    payment_method = models.CharField('Método', max_length=50, blank=True)
    payment_type = models.CharField('Tipo', max_length=50, blank=True)
    amount = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    payer_email = models.EmailField('Email do Pagador', blank=True)
    pix_qr_code = models.TextField('PIX Copia e Cola', blank=True)
    pix_qr_code_base64 = models.TextField('PIX QR Code (base64)', blank=True)
    raw_response = models.JSONField('Resposta Bruta', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Pagamento #{self.order.short_id}'
