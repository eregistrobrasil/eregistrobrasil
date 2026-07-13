from django.contrib import admin
from django.templatetags.static import static
from django.utils.html import format_html

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
    readonly_fields = ('preview_imagem',)
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
        ('Transparência', {
            'fields': ('canal_oficial',),
            'description': (
                'Canal oficial onde o interessado pode solicitar o documento diretamente, '
                'sem intermediação (exibido no aviso de transparência da página do serviço).'
            ),
        }),
        ('Imagem do Serviço', {
            'fields': ('imagem_static', 'preview_imagem'),
            'description': (
                'Informe o caminho relativo dentro de static/. '
                'Ex: img/servicos/certidao-nascimento.webp — '
                'coloque o arquivo em static/img/servicos/ e atualize o campo.'
            ),
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )

    def preview_imagem(self, obj):
        if not obj.imagem_static:
            return '(nenhuma imagem configurada)'
        url = static(obj.imagem_static)
        return format_html(
            '<img src="{}" style="max-width:220px;max-height:160px;'
            'border-radius:8px;border:1px solid #e2e8f0;object-fit:cover;" '
            'onerror="this.style.display=\'none\'" />',
            url,
        )

    preview_imagem.short_description = 'Preview'


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
