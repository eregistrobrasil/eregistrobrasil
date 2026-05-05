import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from products.models import Product


class Cart(models.Model):
    session_key = models.CharField('Sessão', max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Carrinho'
        verbose_name_plural = 'Carrinhos'

    def get_total(self):
        return sum(item.get_total() for item in self.items.all())

    def get_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField('Quantidade', default=1)
    state = models.ForeignKey(
        'products.State', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Estado'
    )
    unit_price = models.DecimalField(
        'Preço Unitário', max_digits=10, decimal_places=2, null=True, blank=True
    )
    requester_name = models.CharField('Nome do Requerente', max_length=200, blank=True)
    requester_document = models.CharField('Documento', max_length=30, blank=True)

    class Meta:
        unique_together = ['cart', 'product']
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens do Carrinho'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def get_total(self):
        price = self.unit_price if self.unit_price is not None else self.product.price
        return price * self.quantity


class Order(models.Model):
    TIPO_CERTIDAO_CHOICES = [
        ('nascimento', 'Certidão de Nascimento'),
        ('casamento', 'Certidão de Casamento'),
        ('obito', 'Certidão de Óbito'),
        ('imovel', 'Certidão de Imóvel'),
        ('interdicao', 'Certidão de Interdição'),
        ('procuracao', 'Certidão de Procuração'),
        ('cnd_federal', 'CND Federal'),
        ('outros', 'Outros'),
    ]

    STATUS_CHOICES = [
        # Fase financeira
        ('pending', 'Aguardando Pagamento'),
        ('paid', 'Pago'),
        # Fase operacional
        ('novo', 'Novo'),
        ('em_analise', 'Em Análise'),
        ('aguardando_documentos', 'Aguardando Documentos'),
        ('em_processamento', 'Em Processamento'),
        ('em_cartorio', 'Em Cartório'),
        ('pronto_envio', 'Pronto para Envio'),
        ('enviado', 'Enviado'),
        # Finais
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
        ('refunded', 'Reembolsado'),
        # Legacy
        ('processing', 'Processando'),
        ('completed', 'Completo'),
    ]

    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    STATUS_CORES = {
        'pending': 'yellow',
        'paid': 'blue',
        'novo': 'indigo',
        'em_analise': 'purple',
        'aguardando_documentos': 'orange',
        'em_processamento': 'blue',
        'em_cartorio': 'cyan',
        'pronto_envio': 'teal',
        'enviado': 'lime',
        'concluido': 'green',
        'cancelado': 'red',
        'refunded': 'gray',
        'processing': 'blue',
        'completed': 'green',
    }

    PRIORIDADE_CORES = {
        'baixa': 'gray',
        'media': 'blue',
        'alta': 'orange',
        'urgente': 'red',
    }

    SLA_HORAS_PADRAO = {
        'nascimento': 120,
        'casamento': 120,
        'obito': 120,
        'imovel': 240,
        'interdicao': 168,
        'procuracao': 96,
        'cnd_federal': 48,
        'outros': 120,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='orders',
        null=True, blank=True
    )
    status = models.CharField('Status', max_length=30, choices=STATUS_CHOICES, default='pending')

    # Dados do cliente
    customer_name = models.CharField('Nome', max_length=200)
    customer_email = models.EmailField('E-mail')
    customer_cpf = models.CharField('CPF', max_length=14)
    customer_phone = models.CharField('Telefone', max_length=20, blank=True)

    # Dados operacionais
    tipo_certidao = models.CharField(
        'Tipo de Certidão', max_length=20, choices=TIPO_CERTIDAO_CHOICES, blank=True
    )
    estado = models.CharField('Estado (UF)', max_length=2, blank=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True)
    cartorio = models.ForeignKey(
        'registry.Registry', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Cartório', related_name='orders'
    )
    prioridade = models.CharField(
        'Prioridade', max_length=10, choices=PRIORIDADE_CHOICES, default='media'
    )
    responsavel = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Responsável', related_name='pedidos_responsavel'
    )
    prazo_entrega = models.DateTimeField('Prazo de Entrega', null=True, blank=True)
    sla_horas = models.PositiveIntegerField('SLA (horas)', null=True, blank=True)
    data_envio = models.DateTimeField('Data de Envio', null=True, blank=True)
    data_conclusao = models.DateTimeField('Data de Conclusão', null=True, blank=True)

    # Financeiro
    subtotal = models.DecimalField('Subtotal', max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, default=0)

    # Pagamento
    payment_id = models.CharField('ID do Pagamento', max_length=200, blank=True)
    payment_method = models.CharField('Método de Pagamento', max_length=50, blank=True)

    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['responsavel', 'status']),
            models.Index(fields=['prazo_entrega']),
        ]

    def __str__(self):
        return f'Pedido #{str(self.id)[:8].upper()}'

    @property
    def short_id(self):
        return str(self.id)[:8].upper()

    @property
    def status_color(self):
        return self.STATUS_CORES.get(self.status, 'gray')

    @property
    def prioridade_color(self):
        return self.PRIORIDADE_CORES.get(self.prioridade, 'gray')

    @property
    def esta_atrasado(self):
        if self.prazo_entrega and self.status not in ('concluido', 'cancelado', 'refunded', 'completed'):
            return timezone.now() > self.prazo_entrega
        return False

    @property
    def horas_restantes(self):
        if self.prazo_entrega and self.status not in ('concluido', 'cancelado', 'refunded', 'completed'):
            delta = self.prazo_entrega - timezone.now()
            return int(delta.total_seconds() / 3600)
        return None

    @property
    def sla_percentual(self):
        if self.sla_horas and self.prazo_entrega:
            total = self.sla_horas * 3600
            restante = max((self.prazo_entrega - timezone.now()).total_seconds(), 0)
            usado = total - restante
            return min(int((usado / total) * 100), 100)
        return 0

    @property
    def sla_cor(self):
        p = self.sla_percentual
        if p >= 90 or self.esta_atrasado:
            return 'red'
        if p >= 70:
            return 'yellow'
        return 'green'

    def definir_prazo_automatico(self):
        if not self.prazo_entrega and self.tipo_certidao:
            horas = self.SLA_HORAS_PADRAO.get(self.tipo_certidao, 120)
            self.sla_horas = horas
            self.prazo_entrega = self.created_at + timezone.timedelta(hours=horas)

    def registrar_log(self, status_novo, usuario=None, observacao=''):
        if self.status != status_novo:
            OrderStatusLog.objects.create(
                order=self,
                status_anterior=self.status,
                status_novo=status_novo,
                usuario=usuario,
                observacao=observacao,
            )


class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='logs')
    status_anterior = models.CharField('Status Anterior', max_length=30)
    status_novo = models.CharField('Novo Status', max_length=30)
    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    observacao = models.TextField('Observação', blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Status'
        verbose_name_plural = 'Histórico de Status'
        ordering = ['-data']

    def __str__(self):
        return f'{self.order.short_id}: {self.status_anterior} → {self.status_novo}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField('Produto', max_length=200)
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Quantidade', default=1)
    requester_name = models.CharField('Nome do Requerente', max_length=200, blank=True)
    requester_document = models.CharField('Documento', max_length=30, blank=True)
    additional_info = models.TextField('Informações Adicionais', blank=True)

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        return f'{self.product_name} x {self.quantity}'

    def get_total(self):
        return self.price * self.quantity
