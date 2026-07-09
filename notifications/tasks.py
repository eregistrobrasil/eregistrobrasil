from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User


@shared_task(name='notifications.verificar_atrasos')
def verificar_atrasos():
    from orders.models import Order
    from .models import Notification

    atrasados = Order.objects.filter(
        prazo_entrega__lt=timezone.now(),
    ).exclude(
        status__in=('concluido', 'cancelado', 'refunded', 'completed')
    ).select_related('responsavel')

    count = 0
    for order in atrasados:
        if order.responsavel:
            ja_notificado = Notification.objects.filter(
                order=order, tipo='atraso',
                data__gte=timezone.now() - timezone.timedelta(hours=4)
            ).exists()
            if not ja_notificado:
                Notification.criar(
                    usuario=order.responsavel,
                    tipo='atraso',
                    mensagem=f'Pedido #{order.short_id} está atrasado. Prazo era {order.prazo_entrega.strftime("%d/%m %H:%M")}.',
                    order=order,
                )
                count += 1
    return f'{count} notificações de atraso criadas'


@shared_task(name='notifications.verificar_prazo_proximo')
def verificar_prazo_proximo():
    from orders.models import Order
    from .models import Notification

    limite = timezone.now() + timezone.timedelta(hours=2)
    proximos = Order.objects.filter(
        prazo_entrega__lte=limite,
        prazo_entrega__gt=timezone.now(),
    ).exclude(
        status__in=('concluido', 'cancelado', 'refunded', 'completed')
    ).select_related('responsavel')

    count = 0
    for order in proximos:
        if order.responsavel:
            ja_notificado = Notification.objects.filter(
                order=order, tipo='prazo_proximo',
                data__gte=timezone.now() - timezone.timedelta(hours=3)
            ).exists()
            if not ja_notificado:
                horas = order.horas_restantes or 0
                Notification.criar(
                    usuario=order.responsavel,
                    tipo='prazo_proximo',
                    mensagem=f'Pedido #{order.short_id} vence em {horas}h. Atenção!',
                    order=order,
                )
                count += 1
    return f'{count} notificações de prazo criadas'


@shared_task(name='notifications.enviar_email_status')
def enviar_email_status(order_id, status_novo):
    from orders.models import Order

    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return 'Pedido não encontrado'

    templates_assunto = {
        'novo': f'Pedido #{order.short_id} recebido — E-Registro Brasil',
        'em_processamento': f'Pedido #{order.short_id} em andamento',
        'enviado': f'Pedido #{order.short_id} enviado!',
        'concluido': f'Pedido #{order.short_id} concluído com sucesso!',
        'cancelado': f'Pedido #{order.short_id} cancelado',
    }

    templates_corpo = {
        'novo': (
            f'Olá {order.customer_name},\n\n'
            f'Recebemos seu pedido #{order.short_id}.\n'
            f'Em breve nossa equipe iniciará o processamento.\n\n'
            f'Obrigado por escolher o E-Registro Brasil!'
        ),
        'em_processamento': (
            f'Olá {order.customer_name},\n\n'
            f'Seu pedido #{order.short_id} está sendo processado pela nossa equipe.\n'
            f'Você será notificado quando houver novidades.\n\n'
            f'Obrigado!'
        ),
        'enviado': (
            f'Olá {order.customer_name},\n\n'
            f'Seu pedido #{order.short_id} foi enviado!\n'
            f'Em breve você receberá o documento.\n\n'
            f'Obrigado por usar o E-Registro Brasil!'
        ),
        'concluido': (
            f'Olá {order.customer_name},\n\n'
            f'Seu pedido #{order.short_id} foi concluído com sucesso.\n'
            f'Obrigado por usar o E-Registro Brasil!\n\n'
            f'Avalie nosso serviço em nosso site.'
        ),
        'cancelado': (
            f'Olá {order.customer_name},\n\n'
            f'Seu pedido #{order.short_id} foi cancelado.\n'
            f'Em caso de dúvidas, entre em contato.\n\n'
            f'E-Registro Brasil'
        ),
    }

    assinatura_privada = (
        '\n\n---\n'
        'A E-Registro Brasil é uma empresa privada de intermediação de certidões e documentos. '
        'Não somos um cartório, órgão público ou entidade governamental — atuamos facilitando '
        'sua solicitação junto ao cartório ou órgão competente.'
    )

    assunto = templates_assunto.get(status_novo)
    corpo = templates_corpo.get(status_novo)
    if corpo:
        corpo += assinatura_privada

    if assunto and corpo and order.customer_email:
        send_mail(
            subject=assunto,
            message=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer_email],
            fail_silently=True,
        )
        return f'Email enviado para {order.customer_email}'
    return 'Nenhum email enviado'
