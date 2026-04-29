import json
import logging
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView
from django.http import HttpResponse
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

        if not settings.MERCADOPAGO_ACCESS_TOKEN:
            # Sem credenciais configuradas: vai direto para página de pendente
            Payment.objects.get_or_create(order=order, defaults={'amount': order.total})
            return render(request, 'payments/select.html', {
                'order': order,
                'mp_public_key': settings.MERCADOPAGO_PUBLIC_KEY,
                'title': 'Escolha a Forma de Pagamento',
            })

        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

        items = []
        for item in order.items.all():
            items.append({
                'title': item.product_name,
                'quantity': item.quantity,
                'unit_price': float(item.price),
                'currency_id': 'BRL',
            })

        preference_data = {
            'items': items,
            'payer': {
                'name': order.customer_name,
                'email': order.customer_email,
            },
            'back_urls': {
                'success': f'{settings.SITE_URL}/pagamentos/sucesso/{order.id}/',
                'failure': f'{settings.SITE_URL}/pagamentos/falha/{order.id}/',
                'pending': f'{settings.SITE_URL}/pagamentos/pendente/{order.id}/',
            },
            'auto_return': 'approved',
            'external_reference': str(order.id),
            'notification_url': f'{settings.SITE_URL}/pagamentos/webhook/',
        }

        preference_response = sdk.preference().create(preference_data)
        preference = preference_response.get('response', {})

        payment, _ = Payment.objects.get_or_create(order=order, defaults={'amount': order.total})
        payment.preference_id = preference.get('id', '')
        payment.save()

        return render(request, 'payments/select.html', {
            'order': order,
            'preference_id': preference.get('id', ''),
            'mp_public_key': settings.MERCADOPAGO_PUBLIC_KEY,
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
class WebhookView(View):
    """Recebe notificações do Mercado Pago."""

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
