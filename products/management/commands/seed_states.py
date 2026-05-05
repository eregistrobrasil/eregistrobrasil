from django.core.management.base import BaseCommand

from products.models import ESTADOS_BR, State


class Command(BaseCommand):
    help = 'Popula a tabela de estados brasileiros (State)'

    def handle(self, *args, **kwargs):
        criados = 0
        for code, name in ESTADOS_BR:
            _, created = State.objects.get_or_create(code=code, defaults={'name': name})
            if created:
                criados += 1

        self.stdout.write(self.style.SUCCESS(
            f'{criados} estado(s) criado(s). Total: {State.objects.count()} estados.'
        ))
