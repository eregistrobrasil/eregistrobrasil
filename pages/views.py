import json
import os
from django.views.generic import TemplateView, FormView
from django.views import View
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.safestring import mark_safe
from .forms import (
    ContactForm,
    CertidaoCartorioForm,
    CertidaoRegistroForm,
    CertidaoObitoForm,
    CertidaoCasamentoForm,
    CertidaoInterdicaoForm,
    CertidaoProcuracaoForm,
    CertidaoPenhorSafraForm,
    CertidaoEscrituraForm,
    CertidaoUniaoEstavelForm,
    PacoteCertidoesCompraVendaForm,
    TIPOS_CERTIDAO_IMOVEL_DICT,
    IMOVEL_FORM_MAP,
)


def _load_estados_cidades():
    json_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'estados_cidades.json')
    with open(json_path, encoding='utf-8') as f:
        return json.load(f)


def _estados_list(dados):
    return [
        {'uf': uf, 'nome': info['nome']}
        for uf, info in sorted(dados.items(), key=lambda x: x[1]['nome'])
    ]


_PASSOS = [
    {'titulo': 'Preencha o formulário', 'descricao': 'Informe o estado, cidade e o cartório onde o registro foi realizado.'},
    {'titulo': 'Confirme o pedido', 'descricao': 'Revise os dados e conclua sua solicitação com segurança.'},
    {'titulo': 'Acompanhe o processo', 'descricao': 'Você receberá atualizações por e-mail durante todo o processo.'},
    {'titulo': 'Receba o documento', 'descricao': 'A certidão será enviada para o endereço cadastrado ou disponibilizada digitalmente.'},
]


# ─────────────────────────────────────────────
#  Views genéricas reutilizáveis (Mixin / Base)
# ─────────────────────────────────────────────

class BaseCertidaoCartorioView(View):
    """
    Etapa 1 genérica: escolha de estado, cidade e cartório.
    Subclasses definem: title, template_name, dados_step_name, redirect_dados_url,
    descricao_servico (opcional), imagem_static (opcional).
    """
    title = ''
    template_name = 'servicos/base_cartorio.html'
    dados_step_name = ''          # nome da URL do passo 2 (pages:xxx_dados)
    descricao_servico = ''
    imagem_static = ''            # ex: 'img/certidao-de-nascimento.png'
    tipo_cartorio = ''            # ex: 'civil', 'notas', 'imoveis', 'protesto'

    def _ctx(self, dados_ec, form):
        return {
            'title': self.title,
            'estados': _estados_list(dados_ec),
            'passos': _PASSOS,
            'form': form,
            'descricao_servico': self.descricao_servico,
            'imagem_static': self.imagem_static,
            'tipo_cartorio': self.tipo_cartorio,
        }

    def get(self, request):
        dados_ec = _load_estados_cidades()
        return render(request, self.template_name, self._ctx(dados_ec, CertidaoCartorioForm()))

    def post(self, request):
        dados_ec = _load_estados_cidades()
        form = CertidaoCartorioForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            estado_uf = cd['estado'].upper()
            estado_nome = dados_ec.get(estado_uf, {}).get('nome', estado_uf)
            request.session['certidao_cartorio'] = {
                'estado_uf': estado_uf,
                'estado_nome': estado_nome,
                'cidade': cd['cidade'],
                'cartorio': cd['cartorio'],
                'cartorio_id': cd.get('cartorio_id'),
            }
            return redirect(self.dados_step_name)
        return render(request, self.template_name, self._ctx(dados_ec, form))


class BaseCertidaoDadosView(View):
    """
    Etapa 2 genérica: dados do registro + resumo lateral.
    Subclasses definem: title, form_class, template_name, product_slug,
    step1_url, has_cpf, date_fields, extra_session_fields.
    """
    title = ''
    form_class = None
    template_name = 'servicos/base_dados.html'
    product_slug = ''
    step1_url = ''                # nome da URL pages:xxx (etapa 1)
    # IDs dos campos de data para aplicar máscara no template
    date_field_ids = ['id_data_nascimento']
    # nomes de campos de data para serializar (date → str)
    date_fields = []
    descricao_step2 = 'Informe os dados constantes na certidão.'

    def _get_cartorio(self, request):
        return request.session.get('certidao_cartorio')

    def _ctx(self, form, cartorio_data):
        return {
            'title': self.title,
            'form': form,
            'cartorio_data': cartorio_data,
            'step1_url': self.step1_url,
            'date_field_ids': mark_safe(json.dumps(self.date_field_ids)),
            'descricao_step2': self.descricao_step2,
        }

    def get(self, request):
        cartorio_data = self._get_cartorio(request)
        if not cartorio_data:
            messages.warning(request, 'Por favor, preencha os dados do cartório primeiro.')
            return redirect(self.step1_url)
        return render(request, self.template_name, self._ctx(self.form_class(), cartorio_data))

    def post(self, request):
        cartorio_data = self._get_cartorio(request)
        if not cartorio_data:
            return redirect(self.step1_url)
        form = self.form_class(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            dados = {}
            for key, val in cd.items():
                if key in self.date_fields and hasattr(val, 'strftime'):
                    dados[key] = val.strftime('%d/%m/%Y')
                else:
                    dados[key] = val or ''
            request.session['certidao_dados'] = dados
            self._add_to_cart(request, cartorio_data, dados)
            # Propaga cartorio_id para o checkout via sessão
            cartorio_id = cartorio_data.get('cartorio_id')
            if cartorio_id:
                request.session['ordem_cartorio_id'] = cartorio_id
            return redirect('orders:checkout')
        return render(request, self.template_name, self._ctx(form, cartorio_data))

    def _add_to_cart(self, request, cartorio_data, dados):
        from products.models import Product, State
        from products.services import obter_preco_por_estado
        from orders.models import Cart, CartItem
        try:
            product = Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get('nome_completo', ''))[:200]
        item.requester_document = str(dados.get('cpf', ''))[:30]

        # Define preço e estado a partir da sessão (anti-fraude: sempre do banco)
        estado_uf = cartorio_data.get('estado_uf', '')
        if estado_uf:
            unit_price = obter_preco_por_estado(product, estado_uf)
            if unit_price is not None:
                item.unit_price = unit_price
            state_obj = State.objects.filter(code=estado_uf).first()
            if state_obj:
                item.state = state_obj

        item.save()


# ─────────────────────────────────────────────
#  Certidão de Nascimento (mantida para compatibilidade)
# ─────────────────────────────────────────────

class CertidaoNascimentoView(BaseCertidaoCartorioView):
    title = 'Certidão de Nascimento 2ª Via — E-Registro Brasil'
    template_name = 'pages/certidao_nascimento.html'
    dados_step_name = 'pages:certidao_nascimento_dados'
    tipo_cartorio = 'civil'
    descricao_servico = 'Certidão de nascimento atualizada para uso em processos, casamentos e outros fins legais.'
    imagem_static = 'img/certidao-de-nascimento.png'
    _product_slug = 'certidao-de-nascimento-2a-via'

    def _ctx(self, dados_ec, form):
        from products.services import get_state_prices_dict
        from products.models import Product
        ctx = super()._ctx(dados_ec, form)
        ctx['passos'] = _PASSOS
        try:
            product = Product.objects.get(slug=self._product_slug, is_active=True)
            ctx['state_prices_json'] = json.dumps(get_state_prices_dict(product))
            ctx['product_base_price'] = str(product.price)
        except Product.DoesNotExist:
            ctx['state_prices_json'] = '{}'
            ctx['product_base_price'] = '0'
        return ctx


class CertidaoDadosView(BaseCertidaoDadosView):
    title = 'Dados do Registro — Certidão de Nascimento 2ª Via'
    form_class = CertidaoRegistroForm
    template_name = 'pages/certidao_dados.html'
    product_slug = 'certidao-de-nascimento-2a-via'
    step1_url = 'pages:certidao_nascimento'
    date_fields = ['data_nascimento']
    date_field_ids = ['id_data_nascimento']
    descricao_step2 = 'Informe os dados da pessoa constante na certidão de nascimento.'


# ─────────────────────────────────────────────
#  Certidão de Óbito
# ─────────────────────────────────────────────

class CertidaoObitoView(BaseCertidaoCartorioView):
    title = 'Certidão de Óbito 2ª Via — E-Registro Brasil'
    template_name = 'servicos/certidao_obito_cartorio.html'
    dados_step_name = 'pages:certidao_obito_dados'
    tipo_cartorio = 'civil'
    descricao_servico = 'Certidão de óbito para fins de inventário, pensão ou outros processos legais.'
    imagem_static = 'img/certidao-de-nascimento.png'
    _product_slug = 'certidao-de-obito-2a-via'

    def _ctx(self, dados_ec, form):
        from products.services import get_state_prices_dict
        from products.models import Product
        ctx = super()._ctx(dados_ec, form)
        ctx['passos'] = _PASSOS
        try:
            product = Product.objects.get(slug=self._product_slug, is_active=True)
            ctx['state_prices_json'] = json.dumps(get_state_prices_dict(product))
            ctx['product_base_price'] = str(product.price)
        except Product.DoesNotExist:
            ctx['state_prices_json'] = '{}'
            ctx['product_base_price'] = '0'
        return ctx


class CertidaoObitoDadosView(BaseCertidaoDadosView):
    title = 'Dados do Registro — Certidão de Óbito 2ª Via'
    form_class = CertidaoObitoForm
    template_name = 'servicos/certidao_obito_dados.html'
    product_slug = 'certidao-de-obito-2a-via'
    step1_url = 'pages:certidao_obito'
    date_fields = ['data_obito']
    date_field_ids = ['id_data_obito']
    descricao_step2 = 'Informe os dados da pessoa constante na certidão de óbito.'

    def _add_to_cart(self, request, cartorio_data, dados):
        from products.services import obter_preco_por_estado
        from products.models import Product, State
        from orders.models import Cart, CartItem
        try:
            product = Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get('nome_completo', ''))[:200]
        item.requester_document = str(dados.get('cpf', ''))[:30]

        estado_uf = cartorio_data.get('estado_uf', '')
        if estado_uf:
            unit_price = obter_preco_por_estado(product, estado_uf)
            if unit_price is not None:
                item.unit_price = unit_price
            state_obj = State.objects.filter(code=estado_uf).first()
            if state_obj:
                item.state = state_obj

        item.save()


# ─────────────────────────────────────────────
#  Certidão de Casamento
# ─────────────────────────────────────────────

class CertidaoCasamentoView(BaseCertidaoCartorioView):
    title = 'Certidão de Casamento 2ª Via — E-Registro Brasil'
    template_name = 'servicos/certidao_casamento_cartorio.html'
    dados_step_name = 'pages:certidao_casamento_dados'
    tipo_cartorio = 'civil'
    descricao_servico = 'Segunda via da certidão de casamento com validade em todo território nacional.'
    imagem_static = 'img/certidao-de-nascimento.png'
    _product_slug = 'certidao-de-casamento-2a-via'

    def _ctx(self, dados_ec, form):
        from products.services import get_state_prices_dict
        from products.models import Product
        ctx = super()._ctx(dados_ec, form)
        ctx['passos'] = _PASSOS
        try:
            product = Product.objects.get(slug=self._product_slug, is_active=True)
            ctx['state_prices_json'] = json.dumps(get_state_prices_dict(product))
            ctx['product_base_price'] = str(product.price)
        except Product.DoesNotExist:
            ctx['state_prices_json'] = '{}'
            ctx['product_base_price'] = '0'
        return ctx


class CertidaoCasamentoDadosView(BaseCertidaoDadosView):
    title = 'Dados do Registro — Certidão de Casamento 2ª Via'
    form_class = CertidaoCasamentoForm
    template_name = 'servicos/certidao_casamento_dados.html'
    product_slug = 'certidao-de-casamento-2a-via'
    step1_url = 'pages:certidao_casamento'
    date_fields = ['data_casamento']
    date_field_ids = ['id_data_casamento']
    descricao_step2 = 'Informe os dados constantes na certidão de casamento.'

    def _add_to_cart(self, request, cartorio_data, dados):
        from products.services import obter_preco_por_estado
        from products.models import Product, State
        from orders.models import Cart, CartItem
        try:
            product = Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get('conjuge_1', ''))[:200]
        item.requester_document = str(dados.get('cpf', ''))[:30]

        estado_uf = cartorio_data.get('estado_uf', '')
        if estado_uf:
            unit_price = obter_preco_por_estado(product, estado_uf)
            if unit_price is not None:
                item.unit_price = unit_price
            state_obj = State.objects.filter(code=estado_uf).first()
            if state_obj:
                item.state = state_obj

        item.save()


# ─────────────────────────────────────────────
#  Certidão de Interdição
# ─────────────────────────────────────────────

class CertidaoInterdicaoView(BaseCertidaoCartorioView):
    title = 'Certidão de Interdição — E-Registro Brasil'
    template_name = 'servicos/certidao_interdicao_cartorio.html'
    dados_step_name = 'pages:certidao_interdicao_dados'
    tipo_cartorio = 'civil'
    descricao_servico = 'Certidão de interdição registrada em cartório.'
    imagem_static = 'img/certidao-de-nascimento.png'
    _product_slug = 'certidao-de-interdicao'

    def _ctx(self, dados_ec, form):
        from products.services import get_state_prices_dict
        from products.models import Product
        ctx = super()._ctx(dados_ec, form)
        ctx['passos'] = _PASSOS
        try:
            product = Product.objects.get(slug=self._product_slug, is_active=True)
            ctx['state_prices_json'] = json.dumps(get_state_prices_dict(product))
            ctx['product_base_price'] = str(product.price)
        except Product.DoesNotExist:
            ctx['state_prices_json'] = '{}'
            ctx['product_base_price'] = '0'
        return ctx


class CertidaoInterdicaoDadosView(BaseCertidaoDadosView):
    title = 'Dados do Registro — Certidão de Interdição'
    form_class = CertidaoInterdicaoForm
    template_name = 'servicos/certidao_interdicao_dados.html'
    product_slug = 'certidao-de-interdicao'
    step1_url = 'pages:certidao_interdicao'
    date_fields = ['data_nascimento']
    date_field_ids = ['id_data_nascimento']
    descricao_step2 = 'Informe os dados do requerente da certidão de interdição.'

    def _ctx(self, form, cartorio_data):
        ctx = super()._ctx(form, cartorio_data)
        ctx['estados'] = _estados_list(_load_estados_cidades())
        return ctx

    def _add_to_cart(self, request, cartorio_data, dados):
        from products.services import obter_preco_por_estado
        from products.models import Product, State
        from orders.models import Cart, CartItem
        try:
            product = Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get('nome_completo', ''))[:200]
        item.requester_document = str(dados.get('cpf', ''))[:30]

        estado_uf = cartorio_data.get('estado_uf', '')
        if estado_uf:
            unit_price = obter_preco_por_estado(product, estado_uf)
            if unit_price is not None:
                item.unit_price = unit_price
            state_obj = State.objects.filter(code=estado_uf).first()
            if state_obj:
                item.state = state_obj

        item.save()


# ─────────────────────────────────────────────
#  Certidão de Procuração
# ─────────────────────────────────────────────

class CertidaoProcuracaoView(BaseCertidaoCartorioView):
    title = 'Certidão de Procuração — E-Registro Brasil'
    template_name = 'servicos/certidao_procuracao_cartorio.html'
    dados_step_name = 'pages:certidao_procuracao_dados'
    tipo_cartorio = 'notas'
    descricao_servico = 'Localização e emissão de certidão de procuração lavrada em cartório de notas.'
    imagem_static = 'img/certidao-de-nascimento.png'
    # Tenta o slug preferido primeiro; fallback para o slug base
    _product_slugs = ['certidao-de-procuracao-1', 'certidao-de-procuracao']

    def _ctx(self, dados_ec, form):
        from products.services import get_state_prices_dict
        from products.models import Product
        ctx = super()._ctx(dados_ec, form)
        ctx['passos'] = _PASSOS
        product = None
        for slug in self._product_slugs:
            try:
                product = Product.objects.get(slug=slug, is_active=True)
                break
            except Product.DoesNotExist:
                continue
        if product:
            ctx['state_prices_json'] = json.dumps(get_state_prices_dict(product))
            ctx['product_base_price'] = str(product.price)
        else:
            ctx['state_prices_json'] = '{}'
            ctx['product_base_price'] = '0'
        return ctx


class CertidaoProcuracaoDadosView(BaseCertidaoDadosView):
    title = 'Dados do Registro — Certidão de Procuração'
    form_class = CertidaoProcuracaoForm
    template_name = 'servicos/certidao_procuracao_dados.html'
    # Tenta o slug preferido primeiro; fallback para o slug base
    product_slug = 'certidao-de-procuracao-1'
    _product_slug_fallback = 'certidao-de-procuracao'
    step1_url = 'pages:certidao_procuracao'
    date_fields = ['data_ato']
    date_field_ids = ['id_data_ato']
    descricao_step2 = 'Informe os dados do outorgante para localização da procuração.'
    tipo_certidao_sessao = 'procuracao'

    def _add_to_cart(self, request, cartorio_data, dados):
        from products.models import Product, State
        from products.services import obter_preco_por_estado
        from orders.models import Cart, CartItem

        # Tenta os dois slugs possíveis
        product = None
        for slug in [self.product_slug, self._product_slug_fallback]:
            try:
                product = Product.objects.get(slug=slug, is_active=True)
                break
            except Product.DoesNotExist:
                continue
        if product is None:
            return

        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get('nome_completo', ''))[:200]
        item.requester_document = str(dados.get('cpf', ''))[:30]

        estado_uf = cartorio_data.get('estado_uf', '')
        if estado_uf:
            unit_price = obter_preco_por_estado(product, estado_uf)
            if unit_price is not None:
                item.unit_price = unit_price
            state_obj = State.objects.filter(code=estado_uf).first()
            if state_obj:
                item.state = state_obj

        item.save()

        # Salva tipo e cidade na sessão para propagar ao pedido durante o checkout
        request.session['ordem_tipo_certidao'] = self.tipo_certidao_sessao
        request.session['ordem_cidade'] = cartorio_data.get('cidade', '')
        request.session['ordem_cartorio_nome'] = cartorio_data.get('cartorio', '')


# ─────────────────────────────────────────────
#  Certidão de Imóvel (fluxo 3 etapas)
# ─────────────────────────────────────────────

_IMOVEL_TIPOS_INFO = [
    {
        'key': 'matricula',
        'label': 'Matrícula',
        'descricao': 'Certidão que comprova a história completa de um imóvel registrado no cartório.',
    },
    {
        'key': 'inteiro_teor',
        'label': 'Certidão de Inteiro Teor e Ônus da Ação',
        'descricao': 'Cópia integral da matrícula, incluindo todos os atos, ônus reais e ações ajuizadas.',
    },
    {
        'key': 'vintenaria',
        'label': 'Vintenária',
        'descricao': 'Certidão que abrange os últimos 20 anos de registro do imóvel, comprovando titularidade e ônus.',
    },
    {
        'key': 'transcricao',
        'label': 'Transcrição',
        'descricao': 'Certidão de imóveis registrados no sistema de transcrição (anterior ao sistema de matrícula).',
    },
    {
        'key': 'doc_arquivado',
        'label': 'Documento Arquivado',
        'descricao': 'Certidão de documento arquivado referenciado por matrícula, registro ou protocolo.',
    },
    {
        'key': 'pacto_antinupcial',
        'label': 'Pacto Antinupcial',
        'descricao': 'Certidão do pacto antinupcial lavrado em cartório de notas e averbado no Registro de Imóveis.',
    },
    {
        'key': 'condominio',
        'label': 'Condomínio',
        'descricao': 'Certidão de registro de condomínio edilício ou de lotes, com especificações e frações ideais.',
    },
    {
        'key': 'livro3_garantias',
        'label': 'Livro 3 – Garantias',
        'descricao': 'Certidão de registro de hipotecas, penhoras e outros direitos reais de garantia inscritos no Livro 3.',
    },
    {
        'key': 'livro3_auxiliar',
        'label': 'Livro 3 – Auxiliar',
        'descricao': 'Certidão do Livro 3 Auxiliar para registros complementares e acessórios de garantias.',
    },
    {
        'key': 'quesitos',
        'label': 'Quesitos',
        'descricao': 'Certidão com respostas a quesitos específicos sobre o imóvel, emitida pelo oficial do cartório.',
    },
]

_IMOVEL_DATE_FIELDS = {
    'transcricao': ['data_emissao'],
}

_IMOVEL_DATE_FIELD_IDS = {
    'transcricao': ['id_data_emissao'],
}

_IMOVEL_DESCRICAO_STEP3 = {
    'matricula':         'Informe o número da matrícula do imóvel.',
    'inteiro_teor':      'Informe o número da matrícula para a certidão de inteiro teor e ônus da ação.',
    'vintenaria':        'Informe o número da matrícula para a certidão vintenária.',
    'transcricao':       'Informe os dados da transcrição e do imóvel.',
    'doc_arquivado':     'Selecione o tipo de referência e informe o número correspondente.',
    'pacto_antinupcial': 'Informe os dados do outorgante do pacto antinupcial.',
    'condominio':        'Informe o nome do condomínio.',
    'livro3_garantias':  'Informe os dados do titular para busca no Livro 3 – Garantias.',
    'livro3_auxiliar':   'Informe os dados do titular para busca no Livro 3 – Auxiliar.',
    'quesitos':          'Informe o número da matrícula para a certidão de quesitos.',
}


class CertidaoImovelView(BaseCertidaoCartorioView):
    """Etapa 1: seleção de estado, cidade e cartório."""
    title = 'Certidão de Imóvel — E-Registro Brasil'
    template_name = 'servicos/certidao_imovel_cartorio.html'
    dados_step_name = 'pages:certidao_imovel_tipo'
    tipo_cartorio = 'imoveis'
    descricao_servico = (
        'Solicite certidões de imóvel, matrículas, transcrições e outros documentos '
        'do Registro de Imóveis com rapidez e segurança.'
    )
    imagem_static = 'img/certidao-de-nascimento.png'
    _product_slug = 'certidao-de-imovel'

    def _ctx(self, dados_ec, form):
        from products.services import get_imovel_prices_dict
        from products.models import Product
        ctx = super()._ctx(dados_ec, form)
        ctx['passos'] = _PASSOS
        # Exibe preços de matrícula como referência padrão na etapa 1
        ctx['state_prices_json'] = json.dumps(get_imovel_prices_dict('matricula'))
        try:
            product = Product.objects.get(slug=self._product_slug, is_active=True)
            ctx['product_base_price'] = str(product.price)
        except Product.DoesNotExist:
            ctx['product_base_price'] = '0'
        return ctx


class CertidaoImovelTipoView(View):
    """Etapa 2: seleção do tipo de certidão (cards clicáveis)."""
    template_name = 'servicos/certidao_imovel_tipo.html'

    def get(self, request):
        cartorio_data = request.session.get('certidao_cartorio')
        if not cartorio_data:
            messages.warning(request, 'Por favor, preencha os dados do cartório primeiro.')
            return redirect('pages:certidao_imovel')
        return render(request, self.template_name, {
            'title': 'Tipo de Certidão — Certidão de Imóvel',
            'cartorio_data': cartorio_data,
            'tipos': _IMOVEL_TIPOS_INFO,
            'step1_url': 'pages:certidao_imovel',
        })

    def post(self, request):
        tipo = request.POST.get('tipo', '').strip()
        if tipo not in IMOVEL_FORM_MAP:
            messages.error(request, 'Selecione um tipo de certidão válido.')
            return redirect('pages:certidao_imovel_tipo')
        request.session['certidao_imovel_tipo'] = tipo
        return redirect('pages:certidao_imovel_dados')


class CertidaoImovelDadosView(View):
    """Etapa 3: formulário dinâmico baseado no tipo selecionado."""
    template_name = 'servicos/certidao_imovel_dados.html'
    product_slug = 'certidao-de-imovel'

    def _ctx(self, request, form, tipo):
        from products.services import obter_preco_imovel
        cartorio_data = request.session.get('certidao_cartorio')
        tipo_label = TIPOS_CERTIDAO_IMOVEL_DICT.get(tipo, tipo)
        date_field_ids = _IMOVEL_DATE_FIELD_IDS.get(tipo, [])
        estado_uf = (cartorio_data or {}).get('estado_uf', '')
        preco = obter_preco_imovel(tipo, estado_uf) if estado_uf else None
        return {
            'title': f'{tipo_label} — Certidão de Imóvel',
            'form': form,
            'cartorio_data': cartorio_data,
            'step1_url': 'pages:certidao_imovel',
            'tipo': tipo,
            'tipo_label': tipo_label,
            'date_field_ids': mark_safe(json.dumps(date_field_ids)),
            'descricao_step2': _IMOVEL_DESCRICAO_STEP3.get(tipo, 'Informe os dados do imóvel.'),
            'preco_display': f'{preco:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') if preco else None,
            'estado_uf': estado_uf,
        }

    def get(self, request):
        cartorio_data = request.session.get('certidao_cartorio')
        tipo = request.session.get('certidao_imovel_tipo')
        if not cartorio_data:
            messages.warning(request, 'Por favor, preencha os dados do cartório primeiro.')
            return redirect('pages:certidao_imovel')
        if not tipo or tipo not in IMOVEL_FORM_MAP:
            messages.warning(request, 'Selecione o tipo de certidão.')
            return redirect('pages:certidao_imovel_tipo')
        return render(request, self.template_name,
                      self._ctx(request, IMOVEL_FORM_MAP[tipo](), tipo))

    def post(self, request):
        cartorio_data = request.session.get('certidao_cartorio')
        tipo = request.session.get('certidao_imovel_tipo')
        if not cartorio_data:
            return redirect('pages:certidao_imovel')
        if not tipo or tipo not in IMOVEL_FORM_MAP:
            return redirect('pages:certidao_imovel_tipo')
        form = IMOVEL_FORM_MAP[tipo](request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            date_fields = _IMOVEL_DATE_FIELDS.get(tipo, [])
            dados = {}
            for key, val in cd.items():
                if key in date_fields and hasattr(val, 'strftime'):
                    dados[key] = val.strftime('%d/%m/%Y')
                else:
                    dados[key] = val or ''
            dados['tipo_certidao'] = tipo
            request.session['certidao_dados'] = dados
            self._add_to_cart(request, cartorio_data, dados)
            return redirect('orders:checkout')
        return render(request, self.template_name, self._ctx(request, form, tipo))

    def _add_to_cart(self, request, cartorio_data, dados):
        from products.models import Product, State
        from products.services import obter_preco_imovel
        from orders.models import Cart, CartItem
        try:
            product = Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        # nome: usa o primeiro campo de identificação disponível
        item.requester_name = str(
            dados.get('nome_completo')
            or dados.get('nome_condominio')
            or ''
        )[:200]
        item.requester_document = str(dados.get('cpf', ''))[:30]

        estado_uf = cartorio_data.get('estado_uf', '')
        tipo_certidao = dados.get('tipo_certidao', '')
        if estado_uf:
            unit_price = obter_preco_imovel(tipo_certidao, estado_uf)
            if unit_price is None:
                # fallback para preço base do produto
                unit_price = product.price
            item.unit_price = unit_price
            state_obj = State.objects.filter(code=estado_uf).first()
            if state_obj:
                item.state = state_obj
        item.save()


# ─────────────────────────────────────────────
#  Certidão de Escritura
# ─────────────────────────────────────────────

class CertidaoEscrituraView(BaseCertidaoCartorioView):
    title = 'Certidão de Escritura — E-Registro Brasil'
    template_name = 'servicos/certidao_escritura_cartorio.html'
    dados_step_name = 'pages:certidao_escritura_dados'
    tipo_cartorio = 'notas'
    descricao_servico = (
        'Solicite a certidão de escritura pública lavrada em cartório de notas. '
        'Atendemos escrituras de compra e venda, doação, inventário, divórcio e outras.'
    )
    imagem_static = 'img/certidao-de-nascimento.png'
    _product_slug = 'certidao-de-escritura'

    def _ctx(self, dados_ec, form):
        from products.services import get_state_prices_dict
        from products.models import Product
        ctx = super()._ctx(dados_ec, form)
        ctx['passos'] = _PASSOS
        try:
            product = Product.objects.get(slug=self._product_slug, is_active=True)
            ctx['state_prices_json'] = json.dumps(get_state_prices_dict(product))
            ctx['product_base_price'] = str(product.price)
        except Product.DoesNotExist:
            ctx['state_prices_json'] = '{}'
            ctx['product_base_price'] = '0'
        return ctx


class CertidaoEscrituraDadosView(BaseCertidaoDadosView):
    title = 'Dados da Escritura — Certidão de Escritura'
    form_class = CertidaoEscrituraForm
    template_name = 'servicos/certidao_escritura_dados.html'
    product_slug = 'certidao-de-escritura'
    step1_url = 'pages:certidao_escritura'
    date_fields = ['data_ato']
    date_field_ids = ['id_data_ato']
    descricao_step2 = 'Informe os dados do outorgante para localização da escritura no cartório.'

    def _add_to_cart(self, request, cartorio_data, dados):
        from products.models import Product, State
        from products.services import obter_preco_por_estado
        from orders.models import Cart, CartItem
        try:
            product = Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get('nome_completo', ''))[:200]
        item.requester_document = str(dados.get('cpf', ''))[:30]

        estado_uf = cartorio_data.get('estado_uf', '')
        if estado_uf:
            unit_price = obter_preco_por_estado(product, estado_uf)
            if unit_price is not None:
                item.unit_price = unit_price
            state_obj = State.objects.filter(code=estado_uf).first()
            if state_obj:
                item.state = state_obj

        item.save()

        # Propaga tipo e cidade para o pedido no checkout
        request.session['ordem_tipo_certidao'] = 'escritura'
        request.session['ordem_cidade'] = cartorio_data.get('cidade', '')
        request.session['ordem_cartorio_nome'] = cartorio_data.get('cartorio', '')


# ─────────────────────────────────────────────
#  Certidão de Escritura de União Estável
# ─────────────────────────────────────────────

class CertidaoUniaoEstavelView(BaseCertidaoCartorioView):
    title = 'Certidão de Escritura de União Estável — E-Registro Brasil'
    template_name = 'servicos/certidao_uniao_estavel_cartorio.html'
    dados_step_name = 'pages:certidao_uniao_estavel_dados'
    tipo_cartorio = 'notas'
    descricao_servico = (
        'Solicite a certidão de escritura de união estável lavrada em cartório de notas. '
        'Comprova juridicamente a existência da união, essencial para heranças, financiamentos e benefícios.'
    )
    imagem_static = 'img/certidao-de-nascimento.png'
    _product_slug = 'certidao-de-escritura-de-uniao-estavel'

    def _ctx(self, dados_ec, form):
        from products.services import get_state_prices_dict
        from products.models import Product
        ctx = super()._ctx(dados_ec, form)
        ctx['passos'] = _PASSOS
        try:
            product = Product.objects.get(slug=self._product_slug, is_active=True)
            ctx['state_prices_json'] = json.dumps(get_state_prices_dict(product))
            ctx['product_base_price'] = str(product.price)
        except Product.DoesNotExist:
            ctx['state_prices_json'] = '{}'
            ctx['product_base_price'] = '0'
        return ctx


class CertidaoUniaoEstavelDadosView(BaseCertidaoDadosView):
    title = 'Dados da Escritura — Certidão de União Estável'
    form_class = CertidaoUniaoEstavelForm
    template_name = 'servicos/certidao_uniao_estavel_dados.html'
    product_slug = 'certidao-de-escritura-de-uniao-estavel'
    step1_url = 'pages:certidao_uniao_estavel'
    date_fields = ['data_ato']
    date_field_ids = ['id_data_ato']
    descricao_step2 = 'Informe os dados do casal para localização da escritura de união estável no cartório.'

    def _add_to_cart(self, request, cartorio_data, dados):
        from products.models import Product, State
        from products.services import obter_preco_por_estado
        from orders.models import Cart, CartItem
        try:
            product = Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get('nome_completo', ''))[:200]
        item.requester_document = str(dados.get('cpf', ''))[:30]

        estado_uf = cartorio_data.get('estado_uf', '')
        if estado_uf:
            unit_price = obter_preco_por_estado(product, estado_uf)
            if unit_price is not None:
                item.unit_price = unit_price
            state_obj = State.objects.filter(code=estado_uf).first()
            if state_obj:
                item.state = state_obj

        item.save()

        request.session['ordem_tipo_certidao'] = 'uniao_estavel'
        request.session['ordem_cidade'] = cartorio_data.get('cidade', '')
        request.session['ordem_cartorio_nome'] = cartorio_data.get('cartorio', '')


# ─────────────────────────────────────────────
#  ESCRITURA — Mixins base reutilizáveis (não instanciar diretamente)
# ─────────────────────────────────────────────

class _EscrituraCartorioMixin(BaseCertidaoCartorioView):
    """
    Mixin compartilhado por todos os serviços de escritura (etapa 1).
    Subclasses definem: title, template_name, dados_step_name,
    descricao_servico, _product_slug.
    """
    imagem_static = 'img/certidao-de-nascimento.png'
    tipo_cartorio = 'notas'

    def _ctx(self, dados_ec, form):
        from products.services import get_state_prices_dict
        from products.models import Product
        ctx = super()._ctx(dados_ec, form)
        ctx['passos'] = _PASSOS
        try:
            product = Product.objects.get(slug=self._product_slug, is_active=True)
            ctx['state_prices_json'] = json.dumps(get_state_prices_dict(product))
            ctx['product_base_price'] = str(product.price)
        except Product.DoesNotExist:
            ctx['state_prices_json'] = '{}'
            ctx['product_base_price'] = '0'
        return ctx


class _EscrituraDadosMixin(BaseCertidaoDadosView):
    """
    Mixin compartilhado por todos os serviços de escritura (etapa 2).
    Subclasses definem: title, template_name, product_slug, step1_url,
    tipo_certidao, descricao_step2.
    """
    form_class = CertidaoEscrituraForm
    date_fields = ['data_ato']
    date_field_ids = ['id_data_ato']
    tipo_certidao = ''

    def _add_to_cart(self, request, cartorio_data, dados):
        from products.models import Product, State
        from products.services import obter_preco_por_estado
        from orders.models import Cart, CartItem
        try:
            product = Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get('nome_completo', ''))[:200]
        item.requester_document = str(dados.get('cpf', ''))[:30]
        estado_uf = cartorio_data.get('estado_uf', '')
        if estado_uf:
            unit_price = obter_preco_por_estado(product, estado_uf)
            if unit_price is not None:
                item.unit_price = unit_price
            state_obj = State.objects.filter(code=estado_uf).first()
            if state_obj:
                item.state = state_obj
        item.save()
        request.session['ordem_tipo_certidao'] = self.tipo_certidao
        request.session['ordem_cidade'] = cartorio_data.get('cidade', '')
        request.session['ordem_cartorio_nome'] = cartorio_data.get('cartorio', '')


# ─────────────────────────────────────────────
#  Certidão de Escritura de Ata Notarial
# ─────────────────────────────────────────────

class CertidaoEscrituraAtaNotarialView(_EscrituraCartorioMixin):
    title = 'Certidão de Escritura de Ata Notarial — E-Registro Brasil'
    template_name = 'servicos/certidao_escritura_ata_notarial_cartorio.html'
    dados_step_name = 'pages:certidao_escritura_ata_notarial_dados'
    descricao_servico = (
        'Solicite a certidão de ata notarial lavrada em cartório de notas. '
        'Documento com fé pública que narra fatos ou situações presenciadas pelo tabelião.'
    )
    _product_slug = 'certidao-de-escritura-de-ata-notarial'


class CertidaoEscrituraAtaNotarialDadosView(_EscrituraDadosMixin):
    title = 'Dados da Certidão — Ata Notarial'
    template_name = 'servicos/certidao_escritura_ata_notarial_dados.html'
    product_slug = 'certidao-de-escritura-de-ata-notarial'
    step1_url = 'pages:certidao_escritura_ata_notarial'
    tipo_certidao = 'escritura_ata_notarial'
    descricao_step2 = 'Informe os dados do requerente para localização da ata notarial no cartório.'


# ─────────────────────────────────────────────
#  Certidão de Escritura de Compra e Venda
# ─────────────────────────────────────────────

class CertidaoEscrituraCompraVendaView(_EscrituraCartorioMixin):
    title = 'Certidão de Escritura de Compra e Venda — E-Registro Brasil'
    template_name = 'servicos/certidao_escritura_compra_venda_cartorio.html'
    dados_step_name = 'pages:certidao_escritura_compra_venda_dados'
    descricao_servico = (
        'Solicite a certidão de escritura de compra e venda lavrada em cartório de notas. '
        'Documento essencial para transferência de imóveis e regularização fundiária.'
    )
    _product_slug = 'certidao-de-escritura-de-compra-e-venda'


class CertidaoEscrituraCompraVendaDadosView(_EscrituraDadosMixin):
    title = 'Dados da Certidão — Compra e Venda'
    template_name = 'servicos/certidao_escritura_compra_venda_dados.html'
    product_slug = 'certidao-de-escritura-de-compra-e-venda'
    step1_url = 'pages:certidao_escritura_compra_venda'
    tipo_certidao = 'escritura_compra_venda'
    descricao_step2 = 'Informe os dados das partes para localização da escritura de compra e venda no cartório.'


# ─────────────────────────────────────────────
#  Certidão de Escritura de Divórcio
# ─────────────────────────────────────────────

class CertidaoEscrituraDivorcioView(_EscrituraCartorioMixin):
    title = 'Certidão de Escritura de Divórcio — E-Registro Brasil'
    template_name = 'servicos/certidao_escritura_divorcio_cartorio.html'
    dados_step_name = 'pages:certidao_escritura_divorcio_dados'
    descricao_servico = (
        'Solicite a certidão de escritura de divórcio extrajudicial lavrada em cartório de notas. '
        'Comprova a dissolução do casamento de forma consensual, com validade jurídica plena.'
    )
    _product_slug = 'certidao-de-escritura-de-divorcio'


class CertidaoEscrituraDivorcioDadosView(_EscrituraDadosMixin):
    title = 'Dados da Certidão — Divórcio'
    template_name = 'servicos/certidao_escritura_divorcio_dados.html'
    product_slug = 'certidao-de-escritura-de-divorcio'
    step1_url = 'pages:certidao_escritura_divorcio'
    tipo_certidao = 'escritura_divorcio'
    descricao_step2 = 'Informe os dados das partes para localização da escritura de divórcio no cartório.'


# ─────────────────────────────────────────────
#  Certidão de Escritura de Doação
# ─────────────────────────────────────────────

class CertidaoEscrituraDoacaoView(_EscrituraCartorioMixin):
    title = 'Certidão de Escritura de Doação — E-Registro Brasil'
    template_name = 'servicos/certidao_escritura_doacao_cartorio.html'
    dados_step_name = 'pages:certidao_escritura_doacao_dados'
    descricao_servico = (
        'Solicite a certidão de escritura de doação lavrada em cartório de notas. '
        'Comprova a transferência gratuita de bens entre pessoas, com validade jurídica plena.'
    )
    _product_slug = 'certidao-de-escritura-de-doacao'


class CertidaoEscrituraDoacaoDadosView(_EscrituraDadosMixin):
    title = 'Dados da Certidão — Doação'
    template_name = 'servicos/certidao_escritura_doacao_dados.html'
    product_slug = 'certidao-de-escritura-de-doacao'
    step1_url = 'pages:certidao_escritura_doacao'
    tipo_certidao = 'escritura_doacao'
    descricao_step2 = 'Informe os dados do doador para localização da escritura de doação no cartório.'


# ─────────────────────────────────────────────
#  Certidão de Escritura de Emancipação
# ─────────────────────────────────────────────

class CertidaoEscrituraEmancipacaoView(_EscrituraCartorioMixin):
    title = 'Certidão de Escritura de Emancipação — E-Registro Brasil'
    template_name = 'servicos/certidao_escritura_emancipacao_cartorio.html'
    dados_step_name = 'pages:certidao_escritura_emancipacao_dados'
    descricao_servico = (
        'Solicite a certidão de escritura de emancipação lavrada em cartório de notas. '
        'Comprova a antecipação da maioridade civil, conferindo plena capacidade jurídica ao menor.'
    )
    _product_slug = 'certidao-de-escritura-de-emancipacao'


class CertidaoEscrituraEmancipacaoDadosView(_EscrituraDadosMixin):
    title = 'Dados da Certidão — Emancipação'
    template_name = 'servicos/certidao_escritura_emancipacao_dados.html'
    product_slug = 'certidao-de-escritura-de-emancipacao'
    step1_url = 'pages:certidao_escritura_emancipacao'
    tipo_certidao = 'escritura_emancipacao'
    descricao_step2 = 'Informe os dados do emancipado para localização da escritura de emancipação no cartório.'


# ─────────────────────────────────────────────
#  Certidão de Escritura de Hipoteca
# ─────────────────────────────────────────────

class CertidaoEscrituraHipotecaView(_EscrituraCartorioMixin):
    title = 'Certidão de Escritura de Hipoteca — E-Registro Brasil'
    template_name = 'servicos/certidao_escritura_hipoteca_cartorio.html'
    dados_step_name = 'pages:certidao_escritura_hipoteca_dados'
    descricao_servico = (
        'Solicite a certidão de escritura de hipoteca lavrada em cartório de notas. '
        'Comprova a constituição de garantia real sobre imóvel para fins creditícios ou judiciais.'
    )
    _product_slug = 'certidao-de-escritura-de-hipoteca'


class CertidaoEscrituraHipotecaDadosView(_EscrituraDadosMixin):
    title = 'Dados da Certidão — Hipoteca'
    template_name = 'servicos/certidao_escritura_hipoteca_dados.html'
    product_slug = 'certidao-de-escritura-de-hipoteca'
    step1_url = 'pages:certidao_escritura_hipoteca'
    tipo_certidao = 'escritura_hipoteca'
    descricao_step2 = 'Informe os dados do devedor para localização da escritura de hipoteca no cartório.'


# ─────────────────────────────────────────────
#  Certidão de Escritura de Inventário
# ─────────────────────────────────────────────

class CertidaoEscrituraInventarioView(_EscrituraCartorioMixin):
    title = 'Certidão de Escritura de Inventário — E-Registro Brasil'
    template_name = 'servicos/certidao_escritura_inventario_cartorio.html'
    dados_step_name = 'pages:certidao_escritura_inventario_dados'
    descricao_servico = (
        'Solicite a certidão de escritura de inventário extrajudicial lavrada em cartório de notas. '
        'Viabiliza a partilha de bens de forma ágil, sem necessidade de processo judicial.'
    )
    _product_slug = 'certidao-de-escritura-de-inventario'


class CertidaoEscrituraInventarioDadosView(_EscrituraDadosMixin):
    title = 'Dados da Certidão — Inventário'
    template_name = 'servicos/certidao_escritura_inventario_dados.html'
    product_slug = 'certidao-de-escritura-de-inventario'
    step1_url = 'pages:certidao_escritura_inventario'
    tipo_certidao = 'escritura_inventario'
    descricao_step2 = 'Informe os dados do inventariado para localização da escritura de inventário no cartório.'


# ─────────────────────────────────────────────
#  Certidão de Escritura de Pacto Antenupcial
# ─────────────────────────────────────────────

class CertidaoEscrituraPactoAntenupcialView(_EscrituraCartorioMixin):
    title = 'Certidão de Escritura de Pacto Antenupcial — E-Registro Brasil'
    template_name = 'servicos/certidao_escritura_pacto_antenupcial_cartorio.html'
    dados_step_name = 'pages:certidao_escritura_pacto_antenupcial_dados'
    descricao_servico = (
        'Solicite a certidão de escritura de pacto antenupcial lavrada em cartório de notas. '
        'Comprova as condições patrimoniais estabelecidas entre os cônjuges antes do casamento.'
    )
    _product_slug = 'certidao-de-escritura-de-pacto-antenupcial'


class CertidaoEscrituraPactoAntenupcialDadosView(_EscrituraDadosMixin):
    title = 'Dados da Certidão — Pacto Antenupcial'
    template_name = 'servicos/certidao_escritura_pacto_antenupcial_dados.html'
    product_slug = 'certidao-de-escritura-de-pacto-antenupcial'
    step1_url = 'pages:certidao_escritura_pacto_antenupcial'
    tipo_certidao = 'escritura_pacto_antenupcial'
    descricao_step2 = 'Informe os dados dos cônjuges para localização do pacto antenupcial no cartório.'


# ─────────────────────────────────────────────
#  Certidão de Escritura de Permuta
# ─────────────────────────────────────────────

class CertidaoEscrituraPermutaView(_EscrituraCartorioMixin):
    title = 'Certidão de Escritura de Permuta — E-Registro Brasil'
    template_name = 'servicos/certidao_escritura_permuta_cartorio.html'
    dados_step_name = 'pages:certidao_escritura_permuta_dados'
    descricao_servico = (
        'Solicite a certidão de escritura de permuta lavrada em cartório de notas. '
        'Comprova a troca de bens entre partes, com toda a formalidade legal exigida.'
    )
    _product_slug = 'certidao-de-escritura-de-permuta'


class CertidaoEscrituraPermutaDadosView(_EscrituraDadosMixin):
    title = 'Dados da Certidão — Permuta'
    template_name = 'servicos/certidao_escritura_permuta_dados.html'
    product_slug = 'certidao-de-escritura-de-permuta'
    step1_url = 'pages:certidao_escritura_permuta'
    tipo_certidao = 'escritura_permuta'
    descricao_step2 = 'Informe os dados das partes para localização da escritura de permuta no cartório.'


# ─────────────────────────────────────────────
#  Certidão de Escritura de Testamento
# ─────────────────────────────────────────────

class CertidaoEscrituraTestamentoView(_EscrituraCartorioMixin):
    title = 'Certidão de Testamento Público — E-Registro Brasil'
    template_name = 'servicos/certidao_escritura_testamento_cartorio.html'
    dados_step_name = 'pages:certidao_escritura_testamento_dados'
    descricao_servico = (
        'Solicite a certidão de testamento público lavrado em cartório de notas. '
        'Comprova a manifestação de última vontade do testador perante o tabelião.'
    )
    _product_slug = 'certidao-de-escritura-de-testamento'


class CertidaoEscrituraTestamentoDadosView(_EscrituraDadosMixin):
    title = 'Dados da Certidão — Testamento'
    template_name = 'servicos/certidao_escritura_testamento_dados.html'
    product_slug = 'certidao-de-escritura-de-testamento'
    step1_url = 'pages:certidao_escritura_testamento'
    tipo_certidao = 'escritura_testamento'
    descricao_step2 = 'Informe os dados do testador para localização do testamento no cartório.'


# ─────────────────────────────────────────────
#  Certidão de Penhor de Safra
# ─────────────────────────────────────────────

class CertidaoPenhorSafraView(BaseCertidaoCartorioView):
    """Etapa 1: seleção de estado, cidade e cartório para Penhor de Safra."""
    title = 'Certidão de Penhor de Safra — E-Registro Brasil'
    template_name = 'servicos/certidao_penhor_safra_cartorio.html'
    tipo_cartorio = 'imoveis'
    dados_step_name = 'pages:certidao_penhor_safra_dados'
    descricao_servico = (
        'Solicite a certidão de penhor de safra registrada em cartório '
        'com agilidade e segurança em todo o Brasil.'
    )
    imagem_static = 'img/certidao-de-nascimento.png'
    _product_slug = 'certidao-de-penhor-de-safra'

    def _ctx(self, dados_ec, form):
        from products.services import get_imovel_prices_dict
        ctx = super()._ctx(dados_ec, form)
        ctx['passos'] = _PASSOS
        ctx['state_prices_json'] = json.dumps(get_imovel_prices_dict('penhor_safra'))
        ctx['product_base_price'] = '0'
        return ctx


class CertidaoPenhorSafraDadosView(BaseCertidaoDadosView):
    """Etapa 2: formulário de dados do Penhor de Safra."""
    title = 'Dados do Pedido — Certidão de Penhor de Safra'
    form_class = CertidaoPenhorSafraForm
    template_name = 'servicos/certidao_penhor_safra_dados.html'
    product_slug = 'certidao-de-penhor-de-safra'
    step1_url = 'pages:certidao_penhor_safra'
    date_fields = ['data_ato']
    date_field_ids = ['id_data_ato']
    descricao_step2 = 'Informe os dados do penhor de safra registrado em cartório.'

    def _add_to_cart(self, request, cartorio_data, dados):
        from products.models import Product, State
        from products.services import obter_preco_imovel
        from orders.models import Cart, CartItem
        try:
            product = Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get('nome_completo', ''))[:200]
        item.requester_document = str(dados.get('cpf', ''))[:30]

        estado_uf = cartorio_data.get('estado_uf', '')
        if estado_uf:
            unit_price = obter_preco_imovel('penhor_safra', estado_uf)
            if unit_price is None:
                unit_price = product.price
            item.unit_price = unit_price
            state_obj = State.objects.filter(code=estado_uf).first()
            if state_obj:
                item.state = state_obj
        item.save()


# ─────────────────────────────────────────────
#  Pacote de Certidões — Compra e Venda de Imóvel
# ─────────────────────────────────────────────

class PacoteCertidoesCompraVendaView(BaseCertidaoCartorioView):
    title = 'Pacote de Certidões — Compra e Venda de Imóvel'
    template_name = 'servicos/pacote_certidoes_compra_venda_cartorio.html'
    dados_step_name = 'pages:pacote_certidoes_compra_venda_dados'
    tipo_cartorio = 'imoveis'
    descricao_servico = 'Pacote completo de certidões necessárias para transações de compra e venda de imóvel.'
    imagem_static = 'img/certidao-de-nascimento.png'
    _product_slug = 'pacote-de-certidoes-compra-e-venda-de-imovel'

    def _ctx(self, dados_ec, form):
        from products.services import get_state_prices_dict
        from products.models import Product
        ctx = super()._ctx(dados_ec, form)
        ctx['passos'] = _PASSOS
        try:
            product = Product.objects.get(slug=self._product_slug, is_active=True)
            ctx['state_prices_json'] = json.dumps(get_state_prices_dict(product))
            ctx['product_base_price'] = str(product.price)
        except Product.DoesNotExist:
            ctx['state_prices_json'] = '{}'
            ctx['product_base_price'] = '159.90'
        return ctx


class PacoteCertidoesCompraVendaDadosView(BaseCertidaoDadosView):
    title = 'Dados do Solicitante — Pacote de Certidões Compra e Venda'
    form_class = PacoteCertidoesCompraVendaForm
    template_name = 'servicos/pacote_certidoes_compra_venda_dados.html'
    product_slug = 'pacote-de-certidoes-compra-e-venda-de-imovel'
    step1_url = 'pages:pacote_certidoes_compra_venda'
    date_fields = []
    date_field_ids = []
    descricao_step2 = 'Informe os dados do solicitante para o pacote de certidões.'


# ─────────────────────────────────────────────
#  Pages institucionais
# ─────────────────────────────────────────────


class AboutView(TemplateView):
    template_name = 'pages/about.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Quem Somos — E-Registro Brasil'
        return ctx


class ContactView(FormView):
    template_name = 'pages/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('pages:contact')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Fale Conosco — E-Registro Brasil'
        return ctx

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            send_mail(
                subject=f"[Contato] {data['subject']}",
                message=f"Nome: {data['name']}\nE-mail: {data['email']}\n\n{data['message']}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass
        messages.success(self.request, 'Mensagem enviada com sucesso! Em breve entraremos em contato.')
        return super().form_valid(form)


class TermsView(TemplateView):
    template_name = 'pages/terms.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Termos de Uso — E-Registro Brasil'
        return ctx


class PrivacyView(TemplateView):
    template_name = 'pages/privacy.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Política de Privacidade — E-Registro Brasil'
        return ctx


class LegalView(TemplateView):
    template_name = 'pages/legal.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Ressalva Legal — E-Registro Brasil'
        return ctx



def _load_estados_cidades():
    json_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'estados_cidades.json')
    with open(json_path, encoding='utf-8') as f:
        return json.load(f)


def _estados_list(dados):
    return [
        {'uf': uf, 'nome': info['nome']}
        for uf, info in sorted(dados.items(), key=lambda x: x[1]['nome'])
    ]


_PASSOS = [
    {'titulo': 'Preencha o formulário', 'descricao': 'Informe o estado, cidade e o cartório onde o registro foi realizado.'},
    {'titulo': 'Confirme o pedido', 'descricao': 'Revise os dados e conclua sua solicitação com segurança.'},
    {'titulo': 'Acompanhe o processo', 'descricao': 'Você receberá atualizações por e-mail durante todo o processo.'},
    {'titulo': 'Receba o documento', 'descricao': 'A certidão será enviada para o endereço cadastrado ou disponibilizada digitalmente.'},
]


class AboutView(TemplateView):
    template_name = 'pages/about.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Quem Somos — E-Registro Brasil'
        return ctx


class ContactView(FormView):
    template_name = 'pages/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('pages:contact')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Fale Conosco — E-Registro Brasil'
        return ctx

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            send_mail(
                subject=f"[Contato] {data['subject']}",
                message=f"Nome: {data['name']}\nE-mail: {data['email']}\n\n{data['message']}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass
        messages.success(self.request, 'Mensagem enviada com sucesso! Em breve entraremos em contato.')
        return super().form_valid(form)


class CertidaoNascimentoView(View):
    template_name = 'pages/certidao_nascimento.html'
    _product_slug = 'certidao-de-nascimento-2a-via'

    def _ctx(self, dados_ec, form):
        from products.models import Product
        from products.services import get_state_prices_dict
        ctx = {
            'title': 'Certidão de Nascimento 2ª Via — E-Registro Brasil',
            'estados': _estados_list(dados_ec),
            'passos': _PASSOS,
            'form': form,
        }
        try:
            product = Product.objects.get(slug=self._product_slug, is_active=True)
            ctx['state_prices_json'] = json.dumps(get_state_prices_dict(product))
            ctx['product_base_price'] = str(product.price)
        except Product.DoesNotExist:
            ctx['state_prices_json'] = '{}'
            ctx['product_base_price'] = '0'
        return ctx

    def get(self, request):
        dados_ec = _load_estados_cidades()
        return render(request, self.template_name, self._ctx(dados_ec, CertidaoCartorioForm()))

    def post(self, request):
        dados_ec = _load_estados_cidades()
        form = CertidaoCartorioForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            estado_uf = cd['estado'].upper()
            estado_nome = dados_ec.get(estado_uf, {}).get('nome', estado_uf)
            request.session['certidao_cartorio'] = {
                'estado_uf': estado_uf,
                'estado_nome': estado_nome,
                'cidade': cd['cidade'],
                'cartorio': cd['cartorio'],
            }
            return redirect('pages:certidao_nascimento_dados')
        return render(request, self.template_name, self._ctx(dados_ec, form))


class CertidaoDadosView(View):
    template_name = 'pages/certidao_dados.html'

    def _get_cartorio(self, request):
        return request.session.get('certidao_cartorio')

    def _ctx(self, form, cartorio_data):
        return {
            'title': 'Dados do Registro — Certidão de Nascimento 2ª Via',
            'form': form,
            'cartorio_data': cartorio_data,
        }

    def get(self, request):
        cartorio_data = self._get_cartorio(request)
        if not cartorio_data:
            messages.warning(request, 'Por favor, preencha os dados do cartório primeiro.')
            return redirect('pages:certidao_nascimento')
        return render(request, self.template_name, self._ctx(CertidaoRegistroForm(), cartorio_data))

    def post(self, request):
        cartorio_data = self._get_cartorio(request)
        if not cartorio_data:
            return redirect('pages:certidao_nascimento')
        form = CertidaoRegistroForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            dados_registro = {
                'nome_completo': cd['nome_completo'],
                'nome_mae': cd['nome_mae'],
                'nome_pai': cd['nome_pai'],
                'data_nascimento': cd['data_nascimento'].strftime('%d/%m/%Y'),
                'numero_livro': cd.get('numero_livro', ''),
                'numero_folha': cd.get('numero_folha', ''),
                'numero_termo': cd.get('numero_termo', ''),
            }
            request.session['certidao_dados'] = dados_registro
            self._add_to_cart(request, cartorio_data, dados_registro)
            return redirect('orders:checkout')
        return render(request, self.template_name, self._ctx(form, cartorio_data))

    def _add_to_cart(self, request, cartorio_data, dados):
        from products.models import Product, State
        from products.services import obter_preco_por_estado
        from orders.models import Cart, CartItem
        try:
            product = Product.objects.get(slug='certidao-de-nascimento-2a-via', is_active=True)
        except Product.DoesNotExist:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = dados.get('nome_completo', '')[:200]
        item.requester_document = ''
        # Preço por estado — sempre do banco (anti-fraude)
        estado_uf = cartorio_data.get('estado_uf', '')
        if estado_uf:
            unit_price = obter_preco_por_estado(product, estado_uf)
            if unit_price is not None:
                item.unit_price = unit_price
            state_obj = State.objects.filter(code=estado_uf).first()
            if state_obj:
                item.state = state_obj
        item.save()


class TermsView(TemplateView):
    template_name = 'pages/terms.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Termos de Uso — E-Registro Brasil'
        return ctx


class PrivacyView(TemplateView):
    template_name = 'pages/privacy.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Política de Privacidade — E-Registro Brasil'
        return ctx


class LegalView(TemplateView):
    template_name = 'pages/legal.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Ressalva Legal — E-Registro Brasil'
        return ctx
