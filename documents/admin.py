from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'order', 'enviado_por', 'data_upload', 'tamanho_bytes')
    list_filter = ('tipo', 'data_upload')
    search_fields = ('order__customer_name', 'nome_original')
    readonly_fields = ('data_upload', 'tamanho_bytes', 'nome_original')
