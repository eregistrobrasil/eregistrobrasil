from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import TipoServico, Product


TIPOS = [
    {'name': 'Segunda Via', 'slug': 'segunda-via', 'description': 'Emissão de segunda via de certidões de registro civil.', 'order': 1},
    {'name': 'Certidão Negativa', 'slug': 'certidao-negativa', 'description': 'Certidões que atestam a inexistência de débitos ou pendências.', 'order': 2},
    {'name': 'Consulta / Pesquisa', 'slug': 'consulta-pesquisa', 'description': 'Busca e pesquisa de informações em cartórios e sistemas oficiais.', 'order': 3},
    {'name': 'Documento Oficial', 'slug': 'documento-oficial', 'description': 'Lavratura ou obtenção de documentos oficiais em cartório.', 'order': 4},
    {'name': 'Tradução / Apostilamento', 'slug': 'traducao-apostilamento', 'description': 'Tradução juramentada e apostilamento de documentos para uso internacional.', 'order': 5},
]

# Mapeamento: parte do slug do produto → slug do tipo
SLUG_TIPO_MAP = {
    'certidao-de-nascimento': 'segunda-via',
    'certidao-de-casamento': 'segunda-via',
    'certidao-de-obito': 'segunda-via',
    'certidao-de-matricula': 'documento-oficial',
    'certidao-de-onus': 'documento-oficial',
    'certidao-de-testamento': 'documento-oficial',
    'certidao-de-imovel': 'documento-oficial',
    'certidao-negativa-de-alienacao': 'certidao-negativa',
    'certidao-negativa-de-debitos': 'certidao-negativa',
    'certidao-negativa-de-acoes': 'certidao-negativa',
    'procuracao': 'documento-oficial',
    'escritura': 'documento-oficial',
    'reconhecimento-de-firma': 'documento-oficial',
    'cnd-federal': 'certidao-negativa',
    'cnd-itr': 'certidao-negativa',
    'cnd-estadual': 'certidao-negativa',
    'certidao-fgts': 'certidao-negativa',
    'certidao-de-protesto': 'certidao-negativa',
    'certidao-de-interdicao': 'documento-oficial',
    'interdicao': 'documento-oficial',
    'certidao-ibama': 'certidao-negativa',
    'certidao-de-embargo': 'certidao-negativa',
    'certidao-de-penhor': 'documento-oficial',
    'certidao-de-propriedade': 'documento-oficial',
    'certidao-de-tributos': 'certidao-negativa',
    'certidao-de-distribuicao': 'certidao-negativa',
    'certidao-de-cumprimento': 'certidao-negativa',
    'certidao-de-debitos': 'certidao-negativa',
    'certidao-de-inquerito': 'certidao-negativa',
    'certidao-de-improbidade': 'certidao-negativa',
    'certidao-de-inelegibilidade': 'certidao-negativa',
    'certidao-de-quitacao': 'certidao-negativa',
    'certidao-do-stj': 'certidao-negativa',
    'certidao-distribuidor': 'certidao-negativa',
    'certidao-de-tribunal': 'certidao-negativa',
    'certidao-de-acoes': 'certidao-negativa',
    'certidao-de-infracoes': 'certidao-negativa',
    'certidao-de-antecedentes': 'certidao-negativa',
    'cnj': 'certidao-negativa',
    'mpf': 'certidao-negativa',
    'mpe': 'certidao-negativa',
    'stf': 'certidao-negativa',
    'stj': 'certidao-negativa',
    'tcu': 'certidao-negativa',
    'tse': 'certidao-negativa',
    'trt': 'certidao-negativa',
    'junta-comercial': 'documento-oficial',
    'cafir': 'consulta-pesquisa',
    'cadastro-de-imoveis': 'consulta-pesquisa',
    'pesquisa-de-protesto': 'consulta-pesquisa',
    'pesquisa-de-bens': 'consulta-pesquisa',
    'busca-em-cartorios': 'consulta-pesquisa',
    'monitoramento': 'consulta-pesquisa',
    'pacote-de-certidoes': 'documento-oficial',
    'compra-e-venda': 'documento-oficial',
    'traducao-juramentada': 'traducao-apostilamento',
    'apostila-de-haia': 'traducao-apostilamento',
}


class Command(BaseCommand):
    help = 'Seed de tipos de serviço e associação com produtos existentes'

    def handle(self, *args, **kwargs):
        # 1. Criar/atualizar tipos
        tipos_criados = 0
        for data in TIPOS:
            tipo, created = TipoServico.objects.update_or_create(
                slug=data['slug'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'order': data['order'],
                },
            )
            if created:
                tipos_criados += 1
                self.stdout.write(self.style.SUCCESS(f'  ✔ Tipo criado: {tipo.name}'))

        self.stdout.write(self.style.SUCCESS(f'\n{tipos_criados} tipo(s) criado(s).\n'))

        # 2. Associar produtos aos tipos via slug
        atualizados = 0
        sem_tipo = []

        for produto in Product.objects.all():
            tipo_slug = None
            for chave, ts in SLUG_TIPO_MAP.items():
                if chave in produto.slug:
                    tipo_slug = ts
                    break

            if tipo_slug:
                try:
                    tipo = TipoServico.objects.get(slug=tipo_slug)
                    Product.objects.filter(pk=produto.pk).update(tipo=tipo)
                    atualizados += 1
                    self.stdout.write(f'  → {produto.name}  ·  {tipo.name}')
                except TipoServico.DoesNotExist:
                    sem_tipo.append(produto.name)
            else:
                sem_tipo.append(produto.name)

        self.stdout.write(self.style.SUCCESS(f'\n{atualizados} produto(s) atualizado(s).'))

        if sem_tipo:
            self.stdout.write(self.style.WARNING('\nProdutos sem tipo mapeado:'))
            for nome in sem_tipo:
                self.stdout.write(f'  ⚠  {nome}')

        self.stdout.write(self.style.SUCCESS('\nSeed de tipos concluído!'))
