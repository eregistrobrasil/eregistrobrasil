from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse, FileResponse
from django.contrib import messages
import os

from orders.models import Order
from .models import Document


@method_decorator(login_required, name='dispatch')
class DocumentUploadView(View):
    def post(self, request, order_pk):
        order = get_object_or_404(Order, pk=order_pk)

        if not (request.user.is_staff or
                hasattr(request.user, 'profile') and
                request.user.profile.tipo in ('admin', 'operador')):
            return HttpResponse('Acesso negado.', status=403)

        arquivos = request.FILES.getlist('arquivos')
        tipo = request.POST.get('tipo', 'outros')
        observacao = request.POST.get('observacao', '')

        if not arquivos:
            messages.error(request, 'Nenhum arquivo enviado.')
            return redirect('dashboard:order_detail', pk=order_pk)

        for arquivo in arquivos:
            versao = Document.objects.filter(order=order, tipo=tipo).count() + 1
            doc = Document(
                order=order,
                arquivo=arquivo,
                tipo=tipo,
                nome_original=arquivo.name,
                tamanho_bytes=arquivo.size,
                versao=versao,
                enviado_por=request.user,
                observacao=observacao,
            )
            doc.save()

        messages.success(request, f'{len(arquivos)} arquivo(s) enviado(s) com sucesso.')
        return redirect('dashboard:order_detail', pk=order_pk)


@method_decorator(login_required, name='dispatch')
class DocumentDeleteView(View):
    def post(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)

        if not (request.user.is_staff or
                hasattr(request.user, 'profile') and
                request.user.profile.tipo in ('admin', 'operador')):
            return HttpResponse('Acesso negado.', status=403)

        order_pk = doc.order_id
        try:
            if doc.arquivo and os.path.isfile(doc.arquivo.path):
                os.remove(doc.arquivo.path)
        except Exception:
            pass
        doc.delete()
        messages.success(request, 'Documento excluído.')
        return redirect('dashboard:order_detail', pk=order_pk)
