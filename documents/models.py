import os
from django.db import models
from django.contrib.auth.models import User


def document_upload_path(instance, filename):
    order_id = str(instance.order_id)[:8]
    return os.path.join('documents', order_id, filename)


class Document(models.Model):
    TIPO_CHOICES = [
        ('requerimento', 'Requerimento'),
        ('rg', 'RG / CNH'),
        ('cpf', 'CPF'),
        ('comprovante_residencia', 'Comprovante de Residência'),
        ('certidao_original', 'Certidão Original'),
        ('procuracao', 'Procuração'),
        ('comprovante_pagamento', 'Comprovante de Pagamento'),
        ('documento_entregue', 'Documento Entregue'),
        ('outros', 'Outros'),
    ]

    order = models.ForeignKey(
        'orders.Order', on_delete=models.CASCADE, related_name='documents'
    )
    arquivo = models.FileField('Arquivo', upload_to=document_upload_path)
    tipo = models.CharField('Tipo', max_length=30, choices=TIPO_CHOICES, default='outros')
    nome_original = models.CharField('Nome do Arquivo', max_length=255, blank=True)
    tamanho_bytes = models.PositiveIntegerField('Tamanho (bytes)', default=0)
    versao = models.PositiveSmallIntegerField('Versão', default=1)
    enviado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents_uploaded'
    )
    observacao = models.CharField('Observação', max_length=255, blank=True)
    data_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-data_upload']

    def __str__(self):
        return f'{self.get_tipo_display()} — Pedido #{str(self.order_id)[:8].upper()}'

    @property
    def is_image(self):
        name = (self.nome_original or '').lower()
        return any(name.endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'))

    @property
    def is_pdf(self):
        return (self.nome_original or '').lower().endswith('.pdf')

    def save(self, *args, **kwargs):
        if not self.nome_original and self.arquivo:
            self.nome_original = os.path.basename(self.arquivo.name)
        super().save(*args, **kwargs)
