from django.db import models
from django.urls import reverse
from django.utils.text import slugify


ESTADOS_BR = [
    ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
    ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
    ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
    ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
    ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
    ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
    ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
]


class State(models.Model):
    code = models.CharField('Sigla', max_length=2, unique=True)
    name = models.CharField('Nome', max_length=50)

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'


class TipoServico(models.Model):
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField('Slug', unique=True, blank=True)
    description = models.TextField('Descrição', blank=True)
    order = models.PositiveIntegerField('Ordem', default=0)

    class Meta:
        verbose_name = 'Tipo de Serviço'
        verbose_name_plural = 'Tipos de Serviço'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField('Slug', unique=True, blank=True)
    description = models.TextField('Descrição', blank=True)
    icon_svg = models.TextField('Ícone SVG', blank=True)
    order = models.PositiveIntegerField('Ordem', default=0)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:category', kwargs={'slug': self.slug})

    @property
    def active_products_count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    TIPO_CARTORIO_CHOICES = [
        ('civil', 'Civil'),
        ('notas', 'Notas'),
        ('imoveis', 'Imóveis'),
        ('protesto', 'Protesto'),
    ]

    name = models.CharField('Nome', max_length=200)
    slug = models.SlugField('Slug', unique=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        related_name='products', verbose_name='Categoria'
    )
    tipo = models.ForeignKey(
        TipoServico, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products', verbose_name='Tipo de Serviço'
    )
    tipo_cartorio = models.CharField(
        'Tipo de Cartório', max_length=20,
        choices=TIPO_CARTORIO_CHOICES, blank=True,
        help_text='Define qual tipo de cartório é utilizado neste serviço.',
    )
    description = models.TextField('Descrição')
    short_description = models.CharField('Descrição Curta', max_length=300, blank=True)
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    original_price = models.DecimalField(
        'Preço Original', max_digits=10, decimal_places=2, null=True, blank=True
    )
    delivery_days = models.PositiveIntegerField('Prazo de Entrega (dias)', default=5)
    is_active = models.BooleanField('Ativo', default=True)
    is_featured = models.BooleanField('Destaque', default=False)
    icon_svg = models.TextField('Ícone SVG', blank=True)
    order = models.PositiveIntegerField('Ordem', default=0)
    meta_title = models.CharField('Meta Título', max_length=200, blank=True)
    meta_description = models.CharField('Meta Descrição', max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'slug': self.slug})

    @property
    def discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            return int((self.original_price - self.price) / self.original_price * 100)
        return 0


class ServiceStatePrice(models.Model):
    service = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='state_prices', verbose_name='Serviço'
    )
    state = models.ForeignKey(
        State, on_delete=models.CASCADE,
        related_name='service_prices', verbose_name='Estado'
    )
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    promotional_price = models.DecimalField(
        'Preço Promocional', max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Preço por Estado'
        verbose_name_plural = 'Preços por Estado'
        unique_together = [('service', 'state')]
        indexes = [
            models.Index(fields=['service', 'state']),
        ]
        ordering = ['state__name']

    def __str__(self):
        return f'{self.service.name} — {self.state.code}: R$ {self.price}'

    @property
    def effective_price(self):
        return self.price

    @property
    def display_price(self):
        return self.promotional_price if self.promotional_price else self.price


class PrecoImovelEstado(models.Model):
    """
    Preço por estado para cada tipo de certidão de imóvel.
    Permite preços distintos por (tipo_certidao, estado), escalável para
    incluir novos tipos futuramente sem alterar ServiceStatePrice.
    """
    tipo_certidao = models.CharField(
        'Tipo de Certidão', max_length=50,
        help_text='Ex: matricula, inteiro_teor, vintenaria, ...',
        db_index=True,
    )
    state = models.ForeignKey(
        State, on_delete=models.CASCADE,
        related_name='imovel_prices', verbose_name='Estado'
    )
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Preço Imóvel por Estado'
        verbose_name_plural = 'Preços Imóvel por Estado'
        unique_together = [('tipo_certidao', 'state')]
        indexes = [
            models.Index(fields=['tipo_certidao', 'state']),
        ]
        ordering = ['tipo_certidao', 'state__name']

    def __str__(self):
        return f'{self.tipo_certidao} — {self.state.code}: R$ {self.price}'
