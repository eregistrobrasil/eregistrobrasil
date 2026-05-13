import json
import logging
import re
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import mercadopago

from orders.models import Order
from .models import Payment

logger = logging.getLogger(__name__)


class CreatePaymentView(View):
    """Cria preferência no Mercado Pago e redireciona para o checkout."""

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        # Verifica se já tem pagamento aprovado
        if hasattr(order, 'payment') and order.payment.status == 'approved':
            return redirect('payments:success', order_id=order.id)

        Payment.objects.get_or_create(order=order, defaults={'amount': order.total})

        order_cpf = re.sub(r'\D', '', order.customer_cpf)
        return render(request, 'payments/select.html', {
            'order': order,
            'mp_public_key': settings.MERCADOPAGO_PUBLIC_KEY,
            'order_amount': str(order.total),
            'order_cpf': order_cpf,
            'title': 'Escolha a Forma de Pagamento',
        })


class PaymentSuccessView(TemplateView):
    template_name = 'payments/success.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['order'] = get_object_or_404(Order, id=self.kwargs['order_id'])
        ctx['title'] = 'Pagamento Aprovado!'
        payment_id = self.request.GET.get('payment_id')
        if payment_id and hasattr(ctx['order'], 'payment'):
            ctx['order'].payment.mercadopago_id = payment_id
            ctx['order'].payment.status = 'approved'
            ctx['order'].payment.save()
            ctx['order'].status = 'paid'
            ctx['order'].save()
        return ctx


class PaymentFailureView(TemplateView):
    template_name = 'payments/failure.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['order'] = get_object_or_404(Order, id=self.kwargs['order_id'])
        ctx['title'] = 'Pagamento Não Aprovado'
        return ctx


class PaymentPendingView(TemplateView):
    template_name = 'payments/pending.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['order'] = get_object_or_404(Order, id=self.kwargs['order_id'])
        ctx['title'] = 'Pagamento em Análise'
        return ctx


@method_decorator(csrf_exempt, name='dispatch')
class ProcessPaymentView(View):
    """Recebe formData do Payment Brick e cria o pagamento via SDK."""

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        if hasattr(order, 'payment') and order.payment.status == 'approved':
            return JsonResponse({
                'status': 'approved',
                'redirect_url': f'/pagamentos/sucesso/{order.id}/',
            })

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Dados inválidos.'}, status=400)

        if not settings.MERCADOPAGO_ACCESS_TOKEN:
            return JsonResponse({'error': 'Gateway não configurado.'}, status=503)

        data['external_reference'] = str(order.id)
        data['notification_url'] = f'{settings.SITE_URL}/pagamentos/webhook/'

        # Garante transaction_amount como float (MP rejeita string)
        try:
            data['transaction_amount'] = float(data.get('transaction_amount', order.total))
        except (TypeError, ValueError):
            data['transaction_amount'] = float(order.total)

        # Completa dados do pagador a partir do pedido (Brick PIX não envia email)
        payer = data.get('payer') or {}
        if not payer.get('email'):
            payer['email'] = order.customer_email
        if not (payer.get('identification') or {}).get('number'):
            cpf_clean = re.sub(r'\D', '', order.customer_cpf)
            payer['identification'] = {'type': 'CPF', 'number': cpf_clean}
        name_parts = order.customer_name.split(None, 1)
        payer.setdefault('first_name', name_parts[0] if name_parts else '')
        payer.setdefault('last_name', name_parts[1] if len(name_parts) > 1 else '')
        data['payer'] = payer

        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        result = sdk.payment().create(data)
        logger.info('MP create payment response: status=%s detail=%s',
                    result.get('response', {}).get('status'),
                    result.get('response', {}).get('status_detail'))
        response = result.get('response', {})

        status = response.get('status', 'rejected')

        payment, _ = Payment.objects.get_or_create(order=order, defaults={'amount': order.total})
        payment.mercadopago_id = str(response.get('id', ''))
        payment.status = status
        payment.status_detail = response.get('status_detail', '')
        payment.payment_method = response.get('payment_method_id', '')
        payment.payment_type = response.get('payment_type_id', '')
        payment.payer_email = (response.get('payer') or {}).get('email', '')
        payment.raw_response = response
        payment.save()

        if status == 'approved':
            order.status = 'paid'
            order.payment_id = str(response.get('id', ''))
            order.save()
            redirect_url = f'/pagamentos/sucesso/{order.id}/'
        elif status in ('in_process', 'pending', 'authorized'):
            redirect_url = f'/pagamentos/pendente/{order.id}/'
        else:
            redirect_url = f'/pagamentos/falha/{order.id}/'

        return JsonResponse({'status': status, 'redirect_url': redirect_url})


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):

    def post(self, request):
        try:
            data = json.loads(request.body)
            topic = data.get('type') or request.GET.get('topic', '')

            if topic == 'payment':
                payment_id = data.get('data', {}).get('id') or request.GET.get('id')
                if payment_id and settings.MERCADOPAGO_ACCESS_TOKEN:
                    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                    mp_payment = sdk.payment().get(payment_id).get('response', {})
                    order_id = mp_payment.get('external_reference')
                    if order_id:
                        try:
                            order = Order.objects.get(id=order_id)
                            payment, _ = Payment.objects.get_or_create(
                                order=order, defaults={'amount': order.total}
                            )
                            payment.mercadopago_id = str(payment_id)
                            payment.status = mp_payment.get('status', 'pending')
                            payment.status_detail = mp_payment.get('status_detail', '')
                            payment.raw_response = mp_payment
                            payment.save()
                            if payment.status == 'approved':
                                order.status = 'paid'
                                order.payment_id = str(payment_id)
                                order.save()
                        except Order.DoesNotExist:
                            logger.warning(f'Pedido {order_id} não encontrado no webhook.')
        except Exception as exc:
            logger.error(f'Erro no webhook MP: {exc}')

        return HttpResponse(status=200)
