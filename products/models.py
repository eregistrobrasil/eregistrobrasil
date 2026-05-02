from django.db import models
from django.urls import reverse
from django.utils.text import slugify


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
