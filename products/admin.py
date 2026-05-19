from django.contrib import admin
from .models import Category, TipoServico, Product, State, ServiceStatePrice, PrecoImovelEstado


@admin.register(TipoServico)
class TipoServicoAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    list_editable = ('order',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_active', 'show_in_nav', 'active_products_count')
    list_editable = ('order', 'is_active', 'show_in_nav')
    list_filter = ('is_active', 'show_in_nav')
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


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    ordering = ('name',)


@admin.register(ServiceStatePrice)
class ServiceStatePriceAdmin(admin.ModelAdmin):
    list_display = ('service', 'state', 'price', 'promotional_price', 'is_active')
    list_editable = ('price', 'promotional_price', 'is_active')
    list_filter = ('is_active', 'state')
    search_fields = ('service__name', 'state__code', 'state__name')
    autocomplete_fields = ('service', 'state')


@admin.register(PrecoImovelEstado)
class PrecoImovelEstadoAdmin(admin.ModelAdmin):
    list_display = ('tipo_certidao', 'state', 'price', 'is_active')
    list_editable = ('price', 'is_active')
    list_filter = ('is_active', 'tipo_certidao', 'state')
    search_fields = ('tipo_certidao', 'state__code', 'state__name')
    autocomplete_fields = ('state',)
    ordering = ('tipo_certidao', 'state__name')
