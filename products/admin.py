from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_active', 'active_products_count')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'delivery_days', 'is_active', 'is_featured', 'order')
    list_editable = ('price', 'is_active', 'is_featured', 'order')
    list_filter = ('is_active', 'is_featured', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'category', 'short_description', 'description')
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
