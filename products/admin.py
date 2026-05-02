from django.contrib import admin
from .models import Category, TipoServico, Product


@admin.register(TipoServico)
class TipoServicoAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    list_editable = ('order',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_active', 'active_products_count')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'tipo', 'price', 'delivery_days', 'is_active', 'is_featured', 'order')
    list_editable = ('price', 'is_active', 'is_featured', 'order')
    list_filter = ('is_active', 'is_featured', 'category', 'tipo')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'category', 'tipo', 'short_description', 'description')
        }),
        ('Preço e Entrega', {
            'fields': ('price', 'original_price', 'delivery_days')
        }),
        ('Configurações', {
            'fields': ('is_active', 'is_featured', 'order', 'icon_svg')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )
