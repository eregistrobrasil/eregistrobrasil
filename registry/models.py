from django.db import models


class Registry(models.Model):
    TIPO_SERVICO_CHOICES = [
        ('civil', 'Civil'),
        ('notas', 'Notas'),
        ('imoveis', 'Imóveis'),
        ('protesto', 'Protesto'),
    ]

    nome = models.CharField('Nome', max_length=200)
    estado = models.CharField('Estado (UF)', max_length=2)
    cidade = models.CharField('Cidade', max_length=100)
    tipo_servico = models.JSONField(
        'Tipos de Serviço',
        default=list,
        help_text='Lista de tipos: civil, notas, imoveis, protesto',
    )
    cnpj = models.CharField('CNPJ', max_length=18, blank=True)
    endereco = models.CharField('Endereço', max_length=300, blank=True)
    email = models.EmailField('E-mail', blank=True)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    contato = models.CharField('Contato', max_length=200, blank=True)
    prazo_medio_dias = models.PositiveIntegerField('Prazo Médio (dias)', default=15)
    observacoes = models.TextField('Observações', blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cartório'
        verbose_name_plural = 'Cartórios'
        ordering = ['estado', 'cidade', 'nome']
        unique_together = [('nome', 'estado', 'cidade')]
        indexes = [
            models.Index(fields=['estado', 'cidade']),
            models.Index(fields=['ativo']),
        ]

    def __str__(self):
        return f'{self.nome} — {self.cidade}/{self.estado}'
