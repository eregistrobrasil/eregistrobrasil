from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    TIPO_CHOICES = [
        ('novo_pedido', 'Novo Pedido'),
        ('status_alterado', 'Status Alterado'),
        ('atraso', 'Pedido Atrasado'),
        ('prazo_proximo', 'Prazo Próximo'),
        ('enviado', 'Pedido Enviado'),
        ('concluido', 'Pedido Concluído'),
        ('documento_recebido', 'Documento Recebido'),
        ('pagamento_aprovado', 'Pagamento Aprovado'),
    ]

    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications'
    )
    tipo = models.CharField('Tipo', max_length=30, choices=TIPO_CHOICES)
    mensagem = models.TextField('Mensagem')
    order = models.ForeignKey(
        'orders.Order', on_delete=models.CASCADE, null=True, blank=True,
        related_name='notifications'
    )
    lida = models.BooleanField('Lida', default=False)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-data']
        indexes = [models.Index(fields=['usuario', 'lida', '-data'])]

    def __str__(self):
        return f'[{self.get_tipo_display()}] {self.usuario.get_full_name() or self.usuario.username}'

    @classmethod
    def criar(cls, usuario, tipo, mensagem, order=None):
        return cls.objects.create(usuario=usuario, tipo=tipo, mensagem=mensagem, order=order)

    @classmethod
    def nao_lidas(cls, usuario):
        return cls.objects.filter(usuario=usuario, lida=False).count()
