from django.core.exceptions import ValidationError
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


# ═════════════════════════════════════════════════════════════════════════════
# Gestão Financeira: Plano de Contas e Lançamentos
# ═════════════════════════════════════════════════════════════════════════════

class ContaContabil(models.Model):
    """
    Conta do Plano de Contas — estrutura hierárquica (sintéticas agrupam,
    analíticas recebem lançamentos).
    """
    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
    ]

    NATUREZA_CHOICES = [
        ('sintetica', 'Sintética (agrupadora)'),
        ('analitica', 'Analítica (recebe lançamentos)'),
    ]

    codigo = models.CharField(
        'Código', max_length=20, unique=True,
        help_text='Código hierárquico. Ex: 1.1.01',
    )
    nome = models.CharField('Nome', max_length=120)
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, db_index=True)
    natureza = models.CharField(
        'Natureza', max_length=10, choices=NATUREZA_CHOICES, default='analitica',
        help_text='Sintéticas apenas agrupam; analíticas recebem lançamentos.',
    )
    parent = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='filhas', verbose_name='Conta Pai',
    )
    descricao = models.TextField('Descrição', blank=True)
    is_active = models.BooleanField('Ativa', default=True)
    is_system = models.BooleanField(
        'Conta do Sistema', default=False,
        help_text='Contas criadas pelo sistema não podem ser excluídas.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conta Contábil'
        verbose_name_plural = 'Plano de Contas'
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['tipo', 'is_active']),
        ]

    def __str__(self):
        return f'{self.codigo} — {self.nome}'

    def clean(self):
        if self.parent_id:
            if self.parent_id == self.pk:
                raise ValidationError({'parent': 'Uma conta não pode ser pai de si mesma.'})
            if self.parent.tipo != self.tipo:
                raise ValidationError({'parent': 'A conta pai deve ser do mesmo tipo (receita/despesa).'})
            # Evita ciclos na hierarquia
            ancestral = self.parent
            while ancestral is not None:
                if ancestral.pk == self.pk:
                    raise ValidationError({'parent': 'Hierarquia inválida: ciclo detectado.'})
                ancestral = ancestral.parent

    @property
    def nivel(self):
        nivel, atual = 0, self.parent
        while atual is not None:
            nivel += 1
            atual = atual.parent
        return nivel

    @property
    def caminho(self):
        """Nome completo com hierarquia. Ex: Receitas > Serviços > Registro Civil"""
        partes, atual = [self.nome], self.parent
        while atual is not None:
            partes.append(atual.nome)
            atual = atual.parent
        return ' > '.join(reversed(partes))

    @property
    def aceita_lancamentos(self):
        return self.natureza == 'analitica'

    def get_descendentes_ids(self):
        """IDs desta conta + todas as descendentes (para agregações)."""
        ids = [self.pk]
        filhas = list(self.filhas.all())
        while filhas:
            conta = filhas.pop()
            ids.append(conta.pk)
            filhas.extend(conta.filhas.all())
        return ids


class ServicoContaReceita(models.Model):
    """
    Vínculo serviço → conta de receita: define em qual conta as vendas
    do serviço são reconhecidas automaticamente.
    """
    service = models.OneToOneField(
        Product, on_delete=models.CASCADE,
        related_name='conta_receita_vinculo', verbose_name='Serviço',
    )
    conta = models.ForeignKey(
        ContaContabil, on_delete=models.PROTECT,
        related_name='servicos_vinculados', verbose_name='Conta de Receita',
        limit_choices_to={'tipo': 'receita', 'natureza': 'analitica'},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Vínculo Serviço → Conta'
        verbose_name_plural = 'Vínculos Serviço → Conta'
        ordering = ['conta__codigo', 'service__name']

    def __str__(self):
        return f'{self.service.name} → {self.conta.codigo}'


class Lancamento(models.Model):
    """
    Lançamento financeiro (receita ou despesa). Pode ser manual ou gerado
    automaticamente a partir de uma venda (Order paga).
    """
    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
    ]

    ORIGEM_CHOICES = [
        ('manual', 'Manual'),
        ('venda', 'Venda (automático)'),
    ]

    FORMA_PAGAMENTO_CHOICES = [
        ('', '—'),
        ('pix', 'PIX'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('boleto', 'Boleto'),
        ('transferencia', 'Transferência'),
        ('dinheiro', 'Dinheiro'),
        ('outro', 'Outro'),
    ]

    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, db_index=True)
    conta = models.ForeignKey(
        ContaContabil, on_delete=models.PROTECT,
        related_name='lancamentos', verbose_name='Conta',
        limit_choices_to={'natureza': 'analitica'},
    )
    descricao = models.CharField('Descrição', max_length=255)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    data_competencia = models.DateField('Data de Competência', db_index=True)
    data_pagamento = models.DateField('Data de Pagamento', null=True, blank=True)
    status = models.CharField(
        'Status', max_length=12, choices=STATUS_CHOICES, default='confirmado', db_index=True,
    )
    forma_pagamento = models.CharField(
        'Forma de Pagamento', max_length=20, choices=FORMA_PAGAMENTO_CHOICES, blank=True,
    )
    origem = models.CharField(
        'Origem', max_length=10, choices=ORIGEM_CHOICES, default='manual', db_index=True,
    )
    order = models.ForeignKey(
        'orders.Order', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lancamentos', verbose_name='Pedido',
    )
    observacoes = models.TextField('Observações', blank=True)
    criado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lancamentos_criados', verbose_name='Criado por',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lançamento'
        verbose_name_plural = 'Lançamentos'
        ordering = ['-data_competencia', '-created_at']
        indexes = [
            models.Index(fields=['tipo', 'status', '-data_competencia']),
            models.Index(fields=['conta', '-data_competencia']),
            models.Index(fields=['origem', 'order']),
        ]

    def __str__(self):
        sinal = '+' if self.tipo == 'receita' else '−'
        return f'{sinal} R$ {self.valor} — {self.descricao}'

    def clean(self):
        if self.valor is not None and self.valor <= 0:
            raise ValidationError({'valor': 'O valor deve ser maior que zero.'})
        if self.conta_id:
            if self.conta.natureza != 'analitica':
                raise ValidationError({'conta': 'Lançamentos só podem ser feitos em contas analíticas.'})
            if self.tipo and self.conta.tipo != self.tipo:
                raise ValidationError({'conta': 'A conta selecionada não corresponde ao tipo do lançamento.'})

    @property
    def valor_assinado(self):
        return self.valor if self.tipo == 'receita' else -self.valor
