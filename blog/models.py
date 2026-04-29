from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse


class BlogCategory(models.Model):
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField('Slug', unique=True, blank=True)

    class Meta:
        verbose_name = 'Categoria do Blog'
        verbose_name_plural = 'Categorias do Blog'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:list') + f'?categoria={self.slug}'


class Post(models.Model):
    title = models.CharField('Título', max_length=300)
    slug = models.SlugField('Slug', unique=True, blank=True)
    category = models.ForeignKey(
        BlogCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='posts', verbose_name='Categoria'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts', verbose_name='Autor'
    )
    cover_image = models.ImageField('Imagem de Capa', upload_to='blog/', blank=True, null=True)
    content = models.TextField('Conteúdo')
    excerpt = models.TextField('Resumo', blank=True, max_length=500)
    is_published = models.BooleanField('Publicado', default=False)
    meta_title = models.CharField('Meta Título', max_length=200, blank=True)
    meta_description = models.CharField('Meta Descrição', max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField('Publicado em', null=True, blank=True)

    class Meta:
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:detail', kwargs={'slug': self.slug})
