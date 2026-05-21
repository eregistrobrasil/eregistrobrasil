import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from products.models import Product


# ─── Categorias do Painel Operacional ───────────────────────────────────────

CATEGORIA_PAINEL_CHOICES = [
    ('registro_civil',      'Registro Civil'),
    ('notas',               'Tabelionato de Notas'),
    ('imoveis',             'Registro de Imóveis'),
    ('protestos',           'Tabelionato de Protestos'),
    ('federais_estaduais',  'Federais e Estaduais'),
    ('busca',               'Busca'),
    ('apostilamento',       'Apostilamento'),
    ('outros',              'Outros'),
]

# Mapa centralizado: tipo_certidao → categoria_painel
TIPO_CERTIDAO_PARA_CATEGORIA = {
    'nascimento':               'registro_civil',
    'casamento':                'registro_civil',
    'obito':                    'registro_civil',
    'interdicao':               'registro_civil',
    'procuracao':               'notas',
    'escritura':                'notas',
    'uniao_estavel':            'notas',
    'escritura_ata_notarial':   'notas',
    'escritura_compra_venda':   'notas',
    'escritura_divorcio':       'notas',
    'escritura_doacao':         'notas',
    'escritura_emancipacao':    'notas',
    'escritura_hipoteca':       'notas',
    'escritura_inventario':     'notas',
    'escritura_pacto_antenupcial': 'notas',
    'escritura_permuta':        'notas',
    'escritura_testamento':     'notas',
    'imovel':                         'imoveis',
    'imovel_matricula_atualizada':   'imoveis',
    'imovel_alienacao_fiduciaria':   'imoveis',
    'imovel_onus_reais':             'imoveis',
    'imovel_pesquisa_bens':          'imoveis',
    'imovel_penhor_safra':           'imoveis',
    'imovel_pacote_compra_venda':    'imoveis',
    'certidao_protesto':        'protestos',
    'busca_protesto':           'protestos',
    # Federais e Estaduais
    'cnd_federal':                              'federais_estaduais',
    'fgts_inss':                                'federais_estaduais',
    'cnd_estadual':                             'federais_estaduais',
    'cnd_itr':                                  'federais_estaduais',
    'cnj_improbidade':                          'federais_estaduais',
    'cafir':                                    'federais_estaduais',
    'ibama_embargos':                           'federais_estaduais',
    'certidao_negativa_acoes_criminais':        'federais_estaduais',
    'certidao_negativa_debitos_ambientais':     'federais_estaduais',
    'certidao_negativa_municipio':              'federais_estaduais',
    'cota_legal_pcds':                          'federais_estaduais',
    'debitos_trabalhistas':                     'federais_estaduais',
    'propriedade_aeronave':                     'federais_estaduais',
    'junta_comercial':                          'federais_estaduais',
    'regularidade_crea':                        'federais_estaduais',
    'antecedentes_criminais':                   'federais_estaduais',
    'tse_quitacao_eleitoral':                   'federais_estaduais',
    'fed_estadual_outros':                      'federais_estaduais',
    'apostila_haia':                             'apostilamento',
    'traducao_juramentada':                     'apostilamento',
    'busca_testamento':                         'busca',
    'outros':                                   'outros',
}

# Mapa canônico: slug do produto → tipo_certidao
# Fonte de verdade quando a sessão não transporta o tipo
PRODUTO_SLUG_PARA_TIPO = {
    # Registro Civil
    'certidao-de-nascimento-2a-via':              'nascimento',
    'certidao-de-casamento-2a-via':               'casamento',
    'certidao-de-obito-2a-via':                   'obito',
    'certidao-de-interdicao':                     'interdicao',
    # Tabelionato de Notas
    'certidao-de-procuracao':                     'procuracao',
    'certidao-de-escritura':                      'escritura',
    'certidao-de-escritura-de-ata-notarial':      'escritura_ata_notarial',
    'certidao-de-escritura-de-compra-e-venda':    'escritura_compra_venda',
    'certidao-de-escritura-de-divorcio':          'escritura_divorcio',
    'certidao-de-escritura-de-doacao':            'escritura_doacao',
    'certidao-de-escritura-de-emancipacao':       'escritura_emancipacao',
    'certidao-de-escritura-de-hipoteca':          'escritura_hipoteca',
    'certidao-de-escritura-de-inventario':        'escritura_inventario',
    'certidao-de-escritura-de-pacto-antenupcial': 'escritura_pacto_antenupcial',
    'certidao-de-escritura-de-permuta':           'escritura_permuta',
    'certidao-de-escritura-de-testamento':        'escritura_testamento',
    'certidao-de-escritura-de-uniao-estavel':     'uniao_estavel',
    # Registro de Imóveis
    'certidao-de-imovel':                              'imovel',
    'certidao-de-matricula-atualizada':                'imovel_matricula_atualizada',
    'certidao-negativa-de-alienacao-fiduciaria':       'imovel_alienacao_fiduciaria',
    'certidao-de-onus-reais':                          'imovel_onus_reais',
    'pesquisa-de-bens':                                'imovel_pesquisa_bens',
    'certidao-de-penhor-de-safra':                     'imovel_penhor_safra',
    'pacote-de-certidoes-compra-e-venda-de-imovel':    'imovel_pacote_compra_venda',
    # Protestos
    'certidao-de-protesto':                       'certidao_protesto',
    'busca-de-protesto':                          'busca_protesto',
    # Federais e Estaduais — slugs reais do banco
    'cnd-federal-receita-federal':                                  'cnd_federal',
    'certidao-negativa-federal':                                    'cnd_federal',
    'certidao-negativa-estadual':                                   'cnd_federal',
    'certidao-fgts-inss':                                           'fgts_inss',
    'certidao-fgtsinss':                                            'fgts_inss',
    'cnd-estadual-sefaz':                                           'cnd_estadual',
    'cnd-itr-receita-federal':                                      'cnd_itr',
    'cnj-improbidade-administrativa-e-inelegibilidade':             'cnj_improbidade',
    'cadastro-de-imoveis-rurais-cafir':                             'cafir',
    'certidao-ibama-certidao-de-embargos':                          'ibama_embargos',
    'certidao-negativa-de-acoes-criminais':                         'certidao_negativa_acoes_criminais',
    'certidao-negativa-de-debitos-ambientais':                      'certidao_negativa_debitos_ambientais',
    'certidao-negativa-municipio':                                  'certidao_negativa_municipio',
    'certidao-de-cumprimento-da-cota-legal-de-pcds':                'cota_legal_pcds',
    'certidao-negativa-de-debitos-trabalhistas':                    'debitos_trabalhistas',
    'certidao-de-propriedade-de-aeronave':                          'propriedade_aeronave',
    'junta-comercial-certidao-da-empresa':                          'junta_comercial',
    'certidao-regularidade-crea':                                   'regularidade_crea',
    'certidao-antecedentes-criminais':                              'antecedentes_criminais',
    'certidao-de-antecedentes-criminais':                           'antecedentes_criminais',
    'tse-certidao-de-quitacao-eleitoral':                           'tse_quitacao_eleitoral',
    # Federais e Estaduais — produtos sem view dedicada
    'certidao-negativa-de-debitos-do-ibama':                        'fed_estadual_outros',
    'certidao-de-distribuicao-estadual-civel-criminal-f':           'fed_estadual_outros',
    'certidao-de-distribuicao-da-justica-federal':                  'fed_estadual_outros',
    'certidao-de-tributos-da-procuradoria-geral-do-esta':           'fed_estadual_outros',
    'mpe-certidao-de-inquerito-civil':                              'fed_estadual_outros',
    'mpe-certidao-de-inquerito-criminal':                           'fed_estadual_outros',
    'mpf-certidao-negativa':                                        'fed_estadual_outros',
    'mt-certidao-de-debitos':                                       'fed_estadual_outros',
    'mt-certidao-de-infracoes-trabalhistas':                        'fed_estadual_outros',
    'stf-certidao-distribuidor':                                    'fed_estadual_outros',
    'stj-certidao-do-stj':                                          'fed_estadual_outros',
    'tcu-certidao-de-tribunal-de-contas':                           'fed_estadual_outros',
    'trt-certidao-de-acoes-trabalhistas-ceat':                      'fed_estadual_outros',
    # Apostilamento
    'apostila-de-haia':                           'apostila_haia',
    'traducao-juramentada':                       'traducao_juramentada',
    # Busca
    'certidao-negativa-de-testamento':            'busca_testamento',
}


class Cart(models.Model):
    session_key = models.CharField('Sessão', max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Carrinho'
        verbose_name_plural = 'Carrinhos'

    def get_total(self):
        return sum(item.get_total() for item in self.items.all())

    def get_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField('Quantidade', default=1)
    state = models.ForeignKey(
        'products.State', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Estado'
    )
    unit_price = models.DecimalField(
        'Preço Unitário', max_digits=10, decimal_places=2, null=True, blank=True
    )
    requester_name = models.CharField('Nome do Requerente', max_length=200, blank=True)
    requester_document = models.CharField('Documento', max_length=30, blank=True)
    tipo_certidao = models.CharField('Tipo de Certidão', max_length=40, blank=True)

    class Meta:
        unique_together = ['cart', 'product']
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens do Carrinho'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def get_total(self):
        price = self.unit_price if self.unit_price is not None else self.product.price
        return price * self.quantity


class Order(models.Model):
    TIPO_CERTIDAO_CHOICES = [
        ('nascimento', 'Certidão de Nascimento'),
        ('casamento', 'Certidão de Casamento'),
        ('obito', 'Certidão de Óbito'),
        ('imovel', 'Certidão de Imóvel'),
        ('imovel_matricula_atualizada', 'Certidão de Matrícula Atualizada'),
        ('imovel_alienacao_fiduciaria', 'Certidão Negativa de Alienação Fiduciária'),
        ('imovel_onus_reais', 'Certidão de Ônus Reais'),
        ('imovel_pesquisa_bens', 'Pesquisa de Bens'),
        ('imovel_penhor_safra', 'Certidão de Penhor de Safra'),
        ('imovel_pacote_compra_venda', 'Pacote Compra e Venda de Imóvel'),
        ('interdicao', 'Certidão de Interdição'),
        ('procuracao', 'Certidão de Procuração'),
        ('escritura', 'Certidão de Escritura'),
        ('uniao_estavel', 'Certidão de Escritura de União Estável'),
        # Variantes de escritura
        ('escritura_ata_notarial', 'Certidão de Escritura de Ata Notarial'),
        ('escritura_compra_venda', 'Certidão de Escritura de Compra e Venda'),
        ('escritura_divorcio', 'Certidão de Escritura de Divórcio'),
        ('escritura_doacao', 'Certidão de Escritura de Doação'),
        ('escritura_emancipacao', 'Certidão de Escritura de Emancipação'),
        ('escritura_hipoteca', 'Certidão de Escritura de Hipoteca'),
        ('escritura_inventario', 'Certidão de Escritura de Inventário'),
        ('escritura_pacto_antenupcial', 'Certidão de Escritura de Pacto Antenupcial'),
        ('escritura_permuta', 'Certidão de Escritura de Permuta'),
        ('escritura_testamento', 'Certidão de Escritura de Testamento'),
        ('cnd_federal', 'CND Federal'),
        # Federais e Estaduais — subtipos
        ('fgts_inss',                               'FGTS / INSS'),
        ('cnd_estadual',                            'CND Estadual'),
        ('cnd_itr',                                 'CND ITR'),
        ('cnj_improbidade',                         'CNJ Improbidade Administrativa'),
        ('cafir',                                   'CAFIR'),
        ('ibama_embargos',                          'IBAMA Embargos'),
        ('certidao_negativa_acoes_criminais',        'Certidão Negativa de Ações Criminais'),
        ('certidao_negativa_debitos_ambientais',     'Certidão Negativa de Débitos Ambientais'),
        ('certidao_negativa_municipio',             'Certidão Negativa Municipal'),
        ('cota_legal_pcds',                         'Cota Legal de PCDs'),
        ('debitos_trabalhistas',                    'Débitos Trabalhistas'),
        ('propriedade_aeronave',                    'Certidão de Propriedade de Aeronave'),
        ('junta_comercial',                         'Junta Comercial'),
        ('regularidade_crea',                       'Regularidade CREA'),
        ('antecedentes_criminais',                  'Antecedentes Criminais'),
        ('tse_quitacao_eleitoral',                  'TSE Quitação Eleitoral'),
        ('fed_estadual_outros',                     'Outros Federais/Estaduais'),
        # Apostilamento
        ('apostila_haia',                            'Apostila de Haia'),
        ('traducao_juramentada',                     'Tradução Juramentada'),
        # Protestos
        ('busca_protesto', 'Busca de Protesto'),
        ('busca_testamento', 'Certidão Negativa de Testamento'),
        ('outros', 'Outros'),
    ]

    STATUS_CHOICES = [
        # Fase financeira
        ('pending', 'Aguardando Pagamento'),
        ('paid', 'Pago'),
        # Fase operacional
        ('novo', 'Novo'),
        ('em_analise', 'Em Análise'),
        ('aguardando_documentos', 'Aguardando Documentos'),
        ('em_processamento', 'Em Processamento'),
        ('em_cartorio', 'Em Cartório'),
        ('pronto_envio', 'Pronto para Envio'),
        ('enviado', 'Enviado'),
        # Finais
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
        ('refunded', 'Reembolsado'),
        # Legacy
        ('processing', 'Processando'),
        ('completed', 'Completo'),
    ]

    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    STATUS_CORES = {
        'pending': 'yellow',
        'paid': 'blue',
        'novo': 'indigo',
        'em_analise': 'purple',
        'aguardando_documentos': 'orange',
        'em_processamento': 'blue',
        'em_cartorio': 'cyan',
        'pronto_envio': 'teal',
        'enviado': 'lime',
        'concluido': 'green',
        'cancelado': 'red',
        'refunded': 'gray',
        'processing': 'blue',
        'completed': 'green',
    }

    PRIORIDADE_CORES = {
        'baixa': 'gray',
        'media': 'blue',
        'alta': 'orange',
        'urgente': 'red',
    }

    SLA_HORAS_PADRAO = {
        'nascimento': 120,
        'casamento': 120,
        'obito': 120,
        'imovel': 240,
        'interdicao': 168,
        'procuracao': 96,
        'cnd_federal': 48,
        'outros': 120,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='orders',
        null=True, blank=True
    )
    status = models.CharField('Status', max_length=30, choices=STATUS_CHOICES, default='pending')

    # Dados do cliente
    customer_name = models.CharField('Nome', max_length=200)
    customer_email = models.EmailField('E-mail')
    customer_cpf = models.CharField('CPF', max_length=14)
    customer_phone = models.CharField('Telefone', max_length=20, blank=True)

    # Dados operacionais
    tipo_certidao = models.CharField(
        'Tipo de Certidão', max_length=40, choices=TIPO_CERTIDAO_CHOICES, blank=True
    )
    estado = models.CharField('Estado (UF)', max_length=2, blank=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True)
    cartorio = models.ForeignKey(
        'registry.Registry', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Cartório', related_name='orders'
    )
    prioridade = models.CharField(
        'Prioridade', max_length=10, choices=PRIORIDADE_CHOICES, default='media'
    )
    responsavel = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Responsável', related_name='pedidos_responsavel'
    )
    prazo_entrega = models.DateTimeField('Prazo de Entrega', null=True, blank=True)
    sla_horas = models.PositiveIntegerField('SLA (horas)', null=True, blank=True)
    data_envio = models.DateTimeField('Data de Envio', null=True, blank=True)
    data_conclusao = models.DateTimeField('Data de Conclusão', null=True, blank=True)

    # Financeiro
    subtotal = models.DecimalField('Subtotal', max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, default=0)

    # Pagamento
    payment_id = models.CharField('ID do Pagamento', max_length=200, blank=True)
    payment_method = models.CharField('Método de Pagamento', max_length=50, blank=True)

    # Categoria operacional (derivada automaticamente de tipo_certidao)
    categoria_painel = models.CharField(
        'Categoria do Painel', max_length=30,
        choices=CATEGORIA_PAINEL_CHOICES, blank=True, db_index=True,
    )

    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['responsavel', 'status']),
            models.Index(fields=['prazo_entrega']),
            models.Index(fields=['categoria_painel', '-created_at']),
            models.Index(fields=['categoria_painel', 'status']),
        ]

    def __str__(self):
        return f'Pedido #{str(self.id)[:8].upper()}'

    def save(self, *args, **kwargs):
        # Auto-deriva a categoria operacional a partir do tipo_certidao
        if self.tipo_certidao:
            self.categoria_painel = TIPO_CERTIDAO_PARA_CATEGORIA.get(
                self.tipo_certidao, 'outros'
            )
        elif not self.categoria_painel:
            self.categoria_painel = 'outros'
        super().save(*args, **kwargs)

    @property
    def short_id(self):
        return str(self.id)[:8].upper()

    @property
    def status_color(self):
        return self.STATUS_CORES.get(self.status, 'gray')

    @property
    def prioridade_color(self):
        return self.PRIORIDADE_CORES.get(self.prioridade, 'gray')

    @property
    def esta_atrasado(self):
        if self.prazo_entrega and self.status not in ('concluido', 'cancelado', 'refunded', 'completed'):
            return timezone.now() > self.prazo_entrega
        return False

    @property
    def horas_restantes(self):
        if self.prazo_entrega and self.status not in ('concluido', 'cancelado', 'refunded', 'completed'):
            delta = self.prazo_entrega - timezone.now()
            return int(delta.total_seconds() / 3600)
        return None

    @property
    def sla_percentual(self):
        if self.sla_horas and self.prazo_entrega:
            total = self.sla_horas * 3600
            restante = max((self.prazo_entrega - timezone.now()).total_seconds(), 0)
            usado = total - restante
            return min(int((usado / total) * 100), 100)
        return 0

    @property
    def sla_cor(self):
        p = self.sla_percentual
        if p >= 90 or self.esta_atrasado:
            return 'red'
        if p >= 70:
            return 'yellow'
        return 'green'

    def definir_prazo_automatico(self):
        if not self.prazo_entrega and self.tipo_certidao:
            horas = self.SLA_HORAS_PADRAO.get(self.tipo_certidao, 120)
            self.sla_horas = horas
            self.prazo_entrega = self.created_at + timezone.timedelta(hours=horas)

    def registrar_log(self, status_novo, usuario=None, observacao=''):
        if self.status != status_novo:
            OrderStatusLog.objects.create(
                order=self,
                status_anterior=self.status,
                status_novo=status_novo,
                usuario=usuario,
                observacao=observacao,
            )


class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='logs')
    status_anterior = models.CharField('Status Anterior', max_length=30)
    status_novo = models.CharField('Novo Status', max_length=30)
    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    observacao = models.TextField('Observação', blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Status'
        verbose_name_plural = 'Histórico de Status'
        ordering = ['-data']

    def __str__(self):
        return f'{self.order.short_id}: {self.status_anterior} → {self.status_novo}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField('Produto', max_length=200)
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Quantidade', default=1)
    requester_name = models.CharField('Nome do Requerente', max_length=200, blank=True)
    requester_document = models.CharField('Documento', max_length=30, blank=True)
    additional_info = models.TextField('Informações Adicionais', blank=True)

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        return f'{self.product_name} x {self.quantity}'

    def get_total(self):
        return self.price * self.quantity
