import uuid
from django.db import models
from django.contrib.auth.models import User
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
    requester_name = models.CharField('Nome do Requerente', max_length=200, blank=True)
    requester_document = models.CharField('Documento', max_length=30, blank=True)

    class Meta:
        unique_together = ['cart', 'product']
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens do Carrinho'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def get_total(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Aguardando Pagamento'),
        ('paid', 'Pago'),
        ('processing', 'Em Processamento'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='orders',
        null=True, blank=True
    )
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')

    # Dados do cliente
    customer_name = models.CharField('Nome', max_length=200)
    customer_email = models.EmailField('E-mail')
    customer_cpf = models.CharField('CPF', max_length=14)
    customer_phone = models.CharField('Telefone', max_length=20, blank=True)

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

    def __str__(self):
        return f'Pedido #{str(self.id)[:8].upper()}'

    @property
    def short_id(self):
        return str(self.id)[:8].upper()

    @property
    def status_color(self):
        colors = {
            'pending': 'yellow',
            'paid': 'blue',
            'processing': 'blue',
            'completed': 'green',
            'cancelled': 'red',
            'refunded': 'gray',
        }
        return colors.get(self.status, 'gray')


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
