"""
Management command: reorganizar_categorias

Objetivo:
  1. Garantir que a categoria 'protesto' exista (cria se necessário).
  2. Transferir todos os produtos da categoria 'protestos' para 'protesto'.
  3. Desativar as categorias: 'protestos', 'pesquisa', 'apostilamento'.

Uso:
  python manage.py reorganizar_categorias
  python manage.py reorganizar_categorias --dry-run   (mostra o que faria sem alterar)
"""

from django.core.management.base import BaseCommand
from products.models import Category, Product


CATEGORIAS_DESATIVAR = ['protestos', 'pesquisa', 'apostilamento']
SLUG_ORIGEM = 'protestos'
SLUG_DESTINO = 'protesto'


class Command(BaseCommand):
    help = 'Reorganiza categorias de protesto e desativa categorias obsoletas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula as alterações sem persistir no banco.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        prefix = '[DRY-RUN] ' if dry_run else ''

        # ── 1. Garantir que a categoria destino exista ──────────────────────
        cat_destino = Category.objects.filter(slug=SLUG_DESTINO).first()
        if cat_destino:
            self.stdout.write(f'{prefix}Categoria destino encontrada: "{cat_destino.name}" (slug={SLUG_DESTINO})')
        else:
            self.stdout.write(self.style.WARNING(
                f'{prefix}Categoria "{SLUG_DESTINO}" não encontrada. '
                f'Será criada automaticamente.'
            ))
            if not dry_run:
                cat_destino = Category.objects.create(
                    name='Tabelionato de Protestos',
                    slug=SLUG_DESTINO,
                    is_active=True,
                    order=50,
                )
                self.stdout.write(self.style.SUCCESS(f'  → Categoria "{SLUG_DESTINO}" criada com id={cat_destino.pk}'))

        # ── 2. Transferir produtos da categoria 'protestos' → 'protesto' ────
        cat_origem = Category.objects.filter(slug=SLUG_ORIGEM).first()
        if cat_origem and cat_destino:
            produtos = Product.objects.filter(category=cat_origem)
            count = produtos.count()
            if count:
                self.stdout.write(f'{prefix}Transferindo {count} produto(s) de "{SLUG_ORIGEM}" → "{SLUG_DESTINO}":')
                for p in produtos:
                    self.stdout.write(f'  · {p.name} (slug={p.slug})')
                if not dry_run:
                    produtos.update(category=cat_destino)
                    self.stdout.write(self.style.SUCCESS(f'  → {count} produto(s) transferido(s).'))
            else:
                self.stdout.write(f'{prefix}Nenhum produto encontrado na categoria "{SLUG_ORIGEM}".')
        elif not cat_origem:
            self.stdout.write(self.style.WARNING(f'{prefix}Categoria origem "{SLUG_ORIGEM}" não encontrada — nada a transferir.'))

        # ── 3. Desativar categorias obsoletas ────────────────────────────────
        for slug in CATEGORIAS_DESATIVAR:
            cat = Category.objects.filter(slug=slug).first()
            if cat:
                if cat.is_active:
                    self.stdout.write(f'{prefix}Desativando categoria: "{cat.name}" (slug={slug})')
                    if not dry_run:
                        cat.is_active = False
                        cat.save(update_fields=['is_active'])
                        self.stdout.write(self.style.SUCCESS(f'  → Desativada.'))
                else:
                    self.stdout.write(f'{prefix}Categoria "{cat.name}" já está inativa.')
            else:
                self.stdout.write(self.style.WARNING(f'{prefix}Categoria com slug "{slug}" não encontrada.'))

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY-RUN: nenhuma alteração foi persistida.'))
        else:
            self.stdout.write(self.style.SUCCESS('Reorganização de categorias concluída.'))
