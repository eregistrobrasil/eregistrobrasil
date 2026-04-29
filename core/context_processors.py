from django.conf import settings
from datetime import date


def site_processor(request):
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_URL': settings.SITE_URL,
        'MP_PUBLIC_KEY': settings.MERCADOPAGO_PUBLIC_KEY,
        'current_year': date.today().year,
    }
