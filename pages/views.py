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
    CertidaoAntecedentesCriminaisForm,
    CndFederalPFForm,
    TseQuitacaoEleitoralForm,
    CndEstadualSefazForm,
    CndItrReceitaFederalForm,
    CnjImprobidadeAdministrativaForm,
    CertidaoNegativaTestamentoForm,
    CertidaoNegativaTestamentoEtapa1Form,
    _ESTADOS_CHOICES,
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
    # Tipo de certidão propagado à sessão para categorização automática do pedido
    tipo_certidao = ''

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
            # Propaga tipo_certidao (quando definido na subclasse) e cidade
            if self.tipo_certidao:
                request.session['ordem_tipo_certidao'] = self.tipo_certidao
            cidade = cartorio_data.get('cidade', '')
            if cidade:
                request.session['ordem_cidade'] = cidade
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
        # Armazena o tipo no CartItem para que o checkout derive a categoria
        # mesmo que a sessão expire antes do envio do formulário
        if self.tipo_certidao:
            item.tipo_certidao = self.tipo_certidao

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
    tipo_certidao = 'nascimento'


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
    tipo_certidao = 'obito'

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
    tipo_certidao = 'casamento'

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
        item.tipo_certidao = self.tipo_certidao  # 'casamento'

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
    tipo_certidao = 'interdicao'

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
    descricao_servico = 'Localização e intermediação da certidão de procuração lavrada em cartório de notas.'
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
        item.tipo_certidao = 'imovel'
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
        item.tipo_certidao = 'imovel_penhor_safra'
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


# ===========================================================================
#  NOVOS SERVICOS - Protestos, Federais/Estaduais, Busca, Apostilamento
# ===========================================================================

from .forms import (
    ProtestoCartorioForm,
    ProtestoDadosForm,
    ServicoFederalEstatualForm,
    BuscaCartorioForm,
    ApostilaHaiaForm,
    TraducaoJuramentadaForm,
    CafirForm,
    CertidaoFgtsInssForm,
    CertidaoIbamaEmbargosForm,
    CertidaoNegativaAcoesCriminaisForm,
    CertidaoNegativaDebitosAmbientaisForm,
    CertidaoNegativaMunicipioForm,
    CotaLegalPcdsForm,
    DebitosTrabalhalistasForm,
    PropriedadeAeronaveForm,
    JuntaComercialCertidaoEmpresaForm,
    CertidaoRegularidadeCreacForm,
)
from products.services import PRECO_FIXO_FEDERAL_ESTADUAL


class BaseServicoSimplesDadosView(View):
    """View generica para servicos sem etapa de cartorio."""
    title = ""
    form_class = None
    template_name = ""
    product_slug = ""
    tipo_certidao_sessao = "outros"
    fixed_price = False

    def _get_product(self):
        from products.models import Product
        try:
            return Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return None

    def _ctx(self, form, product=None):
        from products.services import get_state_prices_dict
        import json as _json
        ctx = {
            "title": self.title,
            "form": form,
            "passos": _PASSOS,
            "fixed_price": self.fixed_price,
        }
        if product:
            ctx["product"] = product
        if self.fixed_price:
            preco = PRECO_FIXO_FEDERAL_ESTADUAL
            ctx["price_display"] = "R$ {:,.2f}".format(preco).replace(",", "X").replace(".", ",").replace("X", ".")
            ctx["state_prices_json"] = "{}"
        else:
            prices = get_state_prices_dict(product) if product else {}
            ctx["state_prices_json"] = _json.dumps(prices)
            ctx["product_base_price"] = str(product.price) if product else "0"
        return ctx

    def get(self, request):
        product = self._get_product()
        return render(request, self.template_name, self._ctx(self.form_class(), product))

    def post(self, request):
        product = self._get_product()
        form = self.form_class(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            dados = {k: v.strftime('%d/%m/%Y') if hasattr(v, 'strftime') else str(v) for k, v in cd.items()}
            dados["tipo_servico"] = self.product_slug
            request.session["certidao_dados"] = dados
            self._add_to_cart(request, dados, product)
            return redirect("orders:checkout")
        return render(request, self.template_name, self._ctx(form, product))

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get("nome_completo", ""))[:200]
        item.requester_document = str(dados.get("cpf_cnpj", "") or dados.get("cpf", ""))[:30]
        if self.fixed_price:
            item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.tipo_certidao = self.tipo_certidao_sessao
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


# ─────────────────────────────────────────────────────────────────────────────
# Protestos — fluxo multi-etapa (etapa 1: cartório / etapa 2: dados)
# ─────────────────────────────────────────────────────────────────────────────

class _BaseProtestoCartorioView(View):
    """Etapa 1 genérica para serviços de protesto — seleção de cartório."""
    title = ''
    template_name = ''
    dados_step_url = ''
    product_slug = ''

    def _get_product(self):
        from products.models import Product
        try:
            return Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return None

    def _ctx(self, dados_ec, form, product=None):
        ctx = {
            'title': self.title,
            'estados': _estados_list(dados_ec),
            'passos': _PASSOS,
            'form': form,
            'tipo_cartorio': 'protesto',
            'imagem_static': 'img/certidao-de-nascimento.png',
        }
        if product:
            from products.services import get_state_prices_dict
            ctx['product'] = product
            ctx['state_prices_json'] = json.dumps(get_state_prices_dict(product))
            ctx['product_base_price'] = str(product.price)
        else:
            ctx['state_prices_json'] = '{}'
            ctx['product_base_price'] = '0'
        return ctx

    def get(self, request):
        dados_ec = _load_estados_cidades()
        product = self._get_product()
        return render(request, self.template_name, self._ctx(dados_ec, ProtestoCartorioForm(), product))

    def post(self, request):
        dados_ec = _load_estados_cidades()
        product = self._get_product()
        form = ProtestoCartorioForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            estado_uf = cd['estado'].upper()
            estado_nome = dados_ec.get(estado_uf, {}).get('nome', estado_uf)
            todos = bool(cd.get('todos_cartorios', False))
            request.session['certidao_cartorio'] = {
                'estado_uf': estado_uf,
                'estado_nome': estado_nome,
                'cidade': cd['cidade'],
                'cartorio': cd.get('cartorio', ''),
                'cartorio_id': cd.get('cartorio_id'),
                'todos_cartorios': todos,
            }
            return redirect(self.dados_step_url)
        return render(request, self.template_name, self._ctx(dados_ec, form, product))


class _BaseProtestoDadosView(BaseCertidaoDadosView):
    """Etapa 2 genérica para serviços de protesto — dados do solicitante."""
    form_class = ProtestoDadosForm
    date_field_ids = []
    date_fields = []
    tipo_certidao_sessao = 'certidao_protesto'
    descricao_step2 = 'Informe seus dados pessoais para a solicitação.'

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
        request.session['ordem_tipo_certidao'] = self.tipo_certidao_sessao
        cartorio_id = cartorio_data.get('cartorio_id')
        if cartorio_id and not cartorio_data.get('todos_cartorios'):
            request.session['ordem_cartorio_id'] = cartorio_id


class CertidaoProtestoCartorioView(_BaseProtestoCartorioView):
    title = 'Certidão de Protesto — E-Registro Brasil'
    template_name = 'servicos/protesto/certidao_protesto_cartorio.html'
    dados_step_url = 'pages:certidao_protesto_dados'
    product_slug = 'certidao-de-protesto'


class CertidaoProtestoDadosView(_BaseProtestoDadosView):
    title = 'Dados do Solicitante — Certidão de Protesto'
    template_name = 'servicos/protesto/certidao_protesto_dados.html'
    product_slug = 'certidao-de-protesto'
    step1_url = 'pages:certidao_protesto'
    descricao_step2 = 'Informe seus dados pessoais para solicitar a certidão de protesto.'
    tipo_certidao_sessao = 'certidao_protesto'


class BuscaProtestoCartorioView(_BaseProtestoCartorioView):
    title = 'Busca de Protesto — E-Registro Brasil'
    template_name = 'servicos/protesto/busca_protesto_cartorio.html'
    dados_step_url = 'pages:busca_protesto_dados'
    product_slug = 'busca-de-protesto'


class BuscaProtestoDadosView(_BaseProtestoDadosView):
    title = 'Dados do Solicitante — Busca de Protesto'
    template_name = 'servicos/protesto/busca_protesto_dados.html'
    product_slug = 'busca-de-protesto'
    step1_url = 'pages:busca_protesto'
    descricao_step2 = 'Informe seus dados pessoais para realizar a busca de protesto.'
    tipo_certidao_sessao = 'busca_protesto'


# Federais e Estaduais
class CndFederalView(BaseServicoSimplesDadosView):
    title = "CND Federal — Receita Federal"
    form_class = CndFederalPFForm
    template_name = "servicos/federais_estaduais/cnd_federal_receita_federal.html"
    product_slug = "cnd-federal-receita-federal"
    tipo_certidao_sessao = "cnd_federal"
    fixed_price = True


class CertidaoFgtsInssView(BaseServicoSimplesDadosView):
    title = "Certidão FGTS / INSS — E-Registro Brasil"
    form_class = CertidaoFgtsInssForm
    template_name = "servicos/federais_estaduais/certidao-fgts-inss.html"
    product_slug = "certidao-fgts-inss"
    tipo_certidao_sessao = "fgts_inss"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_document = str(dados.get("cnpj", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class CndEstadualView(BaseServicoSimplesDadosView):
    title = "CND Estadual SEFAZ — E-Registro Brasil"
    form_class = CndEstadualSefazForm
    template_name = "servicos/federais_estaduais/cnd_estadual_sefaz.html"
    product_slug = "cnd-estadual-sefaz"
    tipo_certidao_sessao = "cnd_estadual"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_document = str(dados.get("cpf", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class CndItrReceitaFederalView(BaseServicoSimplesDadosView):
    title = "CND ITR — Receita Federal"
    form_class = CndItrReceitaFederalForm
    template_name = "servicos/federais_estaduais/cnd_itr_receita_federal.html"
    product_slug = "cnd-itr-receita-federal"
    tipo_certidao_sessao = "cnd_itr"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_document = str(dados.get("nirf", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class CnjImprobidadeAdministrativaView(BaseServicoSimplesDadosView):
    title = "CNJ — Improbidade Administrativa e Inelegibilidade"
    form_class = CnjImprobidadeAdministrativaForm
    template_name = "servicos/federais_estaduais/cnj_improbidade_administrativa.html"
    product_slug = "cnj-improbidade-administrativa-e-inelegibilidade"
    tipo_certidao_sessao = "cnj_improbidade"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_document = str(dados.get("cpf", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class CafirView(BaseServicoSimplesDadosView):
    title = "Cadastro de Imóveis Rurais CAFIR — E-Registro Brasil"
    form_class = CafirForm
    template_name = "servicos/federais_estaduais/cadastro-de-imoveis-rurais-cafir.html"
    product_slug = "cadastro-de-imoveis-rurais-cafir"
    tipo_certidao_sessao = "cafir"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_document = str(dados.get("nirf_cib", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class CertidaoIbamaEmbargosView(BaseServicoSimplesDadosView):
    title = "Certidão IBAMA — Certidão de Embargos | E-Registro Brasil"
    form_class = CertidaoIbamaEmbargosForm
    template_name = "servicos/federais_estaduais/certidao-ibama-certidao-de-embargos.html"
    product_slug = "certidao-ibama-certidao-de-embargos"
    tipo_certidao_sessao = "ibama_embargos"
    fixed_price = True

    def _ctx(self, form, product=None):
        ctx = super()._ctx(form, product)
        ctx["estados"] = _estados_list(_load_estados_cidades())
        return ctx

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get("nome_completo", ""))[:200]
        item.requester_document = str(dados.get("cpf", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class CertidaoNegativaAcoesCriminaisView(BaseServicoSimplesDadosView):
    title = "Certidão Negativa de Ações Criminais — E-Registro Brasil"
    form_class = CertidaoNegativaAcoesCriminaisForm
    template_name = "servicos/federais_estaduais/certidao-negativa-de-acoes-criminais.html"
    product_slug = "certidao-negativa-de-acoes-criminais"
    tipo_certidao_sessao = "certidao_negativa_acoes_criminais"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get("nome_completo", ""))[:200]
        item.requester_document = str(dados.get("cpf", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class CertidaoNegativaDebitosAmbientaisView(BaseServicoSimplesDadosView):
    title = "Certidão Negativa de Débitos Ambientais — E-Registro Brasil"
    form_class = CertidaoNegativaDebitosAmbientaisForm
    template_name = "servicos/federais_estaduais/certidao-negativa-de-debitos-ambientais.html"
    product_slug = "certidao-negativa-de-debitos-ambientais"
    tipo_certidao_sessao = "certidao_negativa_debitos_ambientais"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = ""
        item.requester_document = str(dados.get("cpf", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class CertidaoNegativaMunicipioView(BaseServicoSimplesDadosView):
    title = "Certidão Negativa de Débitos Municipais — E-Registro Brasil"
    form_class = CertidaoNegativaMunicipioForm
    template_name = "servicos/federais_estaduais/certidao-negativa-municipio.html"
    product_slug = "certidao-negativa-municipio"
    tipo_certidao_sessao = "certidao_negativa_municipio"
    fixed_price = True

    def _ctx(self, form, product=None):
        ctx = super()._ctx(form, product)
        ctx["estados"] = _estados_list(_load_estados_cidades())
        return ctx

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = ""
        item.requester_document = str(dados.get("cpf", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class CotaLegalPcdsView(BaseServicoSimplesDadosView):
    title = "Certidão de Cumprimento da Cota Legal de PCDs — E-Registro Brasil"
    form_class = CotaLegalPcdsForm
    template_name = "servicos/federais_estaduais/certidao-de-cumprimento-da-cota-legal-de-pcds.html"
    product_slug = "certidao-de-cumprimento-da-cota-legal-de-pcds"
    tipo_certidao_sessao = "cota_legal_pcds"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = ""
        item.requester_document = str(dados.get("cnpj", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class DebitosTrabalhalistasView(BaseServicoSimplesDadosView):
    title = "Certidão Negativa de Débitos Trabalhistas — E-Registro Brasil"
    form_class = DebitosTrabalhalistasForm
    template_name = "servicos/federais_estaduais/certidao-negativa-de-debitos-trabalhistas.html"
    product_slug = "certidao-negativa-de-debitos-trabalhistas"
    tipo_certidao_sessao = "debitos_trabalhistas"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = ""
        item.requester_document = str(dados.get("cpf", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class PropriedadeAeronaveView(BaseServicoSimplesDadosView):
    title = "Certidão de Propriedade de Aeronave — E-Registro Brasil"
    form_class = PropriedadeAeronaveForm
    template_name = "servicos/federais_estaduais/certidao-de-propriedade-de-aeronave.html"
    product_slug = "certidao-de-propriedade-de-aeronave"
    tipo_certidao_sessao = "propriedade_aeronave"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get("nome_razao_social", ""))[:200]
        item.requester_document = str(dados.get("cpf_cnpj", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class JuntaComercialCertidaoEmpresaView(BaseServicoSimplesDadosView):
    title = "Junta Comercial — Certidão da Empresa — E-Registro Brasil"
    form_class = JuntaComercialCertidaoEmpresaForm
    template_name = "servicos/federais_estaduais/junta-comercial-certidao-da-empresa.html"
    product_slug = "junta-comercial-certidao-da-empresa"
    tipo_certidao_sessao = "junta_comercial"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_document = str(dados.get("cnpj", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class CertidaoRegularidadeCreView(BaseServicoSimplesDadosView):
    title = "Certidão de Regularidade no CREA — E-Registro Brasil"
    form_class = CertidaoRegularidadeCreacForm
    template_name = "servicos/federais_estaduais/certidao-regularidade-crea.html"
    product_slug = "certidao-regularidade-crea"
    tipo_certidao_sessao = "regularidade_crea"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get("nome_completo", ""))[:200]
        item.requester_document = str(dados.get("cpf", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


class CertidaoAntecedentesCriminaisView(BaseServicoSimplesDadosView):
    title = "Certidão de Antecedentes Criminais — E-Registro Brasil"
    form_class = CertidaoAntecedentesCriminaisForm
    template_name = "servicos/federais_estaduais/certidao_antecedentes_criminais.html"
    product_slug = "certidao-antecedentes-criminais"
    tipo_certidao_sessao = "antecedentes_criminais"
    fixed_price = True


class TseQuitacaoEleitoralView(BaseServicoSimplesDadosView):
    title = "TSE — Certidão de Quitação Eleitoral"
    form_class = TseQuitacaoEleitoralForm
    template_name = "servicos/federais_estaduais/tse_certidao_quitacao_eleitoral.html"
    product_slug = "tse-certidao-de-quitacao-eleitoral"
    tipo_certidao_sessao = "tse_quitacao_eleitoral"
    fixed_price = True

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get("nome_eleitor", ""))[:200]
        item.requester_document = str(dados.get("titulo_cpf", ""))[:30]
        item.unit_price = PRECO_FIXO_FEDERAL_ESTADUAL
        item.save()
        request.session["ordem_tipo_certidao"] = self.tipo_certidao_sessao


# Busca em Cartorios
class BuscaCartorioRegistroCivilView(BaseServicoSimplesDadosView):
    title = "Busca em Cartorios de Registro Civil - E-Registro Brasil"
    form_class = BuscaCartorioForm
    template_name = "servicos/busca_cartorio.html"
    product_slug = "busca-em-cartorios-registro-civil"


class BuscaTabelionatoNotasView(BaseServicoSimplesDadosView):
    title = "Busca em Tabelionatos de Notas - E-Registro Brasil"
    form_class = BuscaCartorioForm
    template_name = "servicos/busca_cartorio.html"
    product_slug = "busca-em-tabelionatos-notas"


# Apostilamento
class ApostilaHaiaView(BaseServicoSimplesDadosView):
    title = "Apostila de Haia - E-Registro Brasil"
    form_class = ApostilaHaiaForm
    template_name = "servicos/apostila_haia.html"
    product_slug = "apostila-de-haia"
    tipo_certidao_sessao = "apostila_haia"


class TraducaoJuramentadaView(BaseServicoSimplesDadosView):
    title = "Traducao Juramentada - E-Registro Brasil"
    form_class = TraducaoJuramentadaForm
    template_name = "servicos/traducao_juramentada.html"
    product_slug = "traducao-juramentada"
    tipo_certidao_sessao = "traducao_juramentada"


# ===========================================================================
#  VARIANTES DE REGISTRO DE IMÓVEIS
#  Serviços: alienacao-fiduciaria, matricula-atualizada, onus-reais, pesquisa-bens
#  Fluxo: Cartório (step1) → Formulário (step2) → Checkout
#  Precificação: PrecoImovelEstado (mesma tabela da certidão-de-imovel)
# ===========================================================================


class BaseImovelVarianteView(BaseCertidaoCartorioView):
    """
    Etapa 1 genérica para variantes do Registro de Imóveis.
    Herda BaseCertidaoCartorioView, filtra cartórios por tipo='imoveis'.
    Usa ServiceStatePrice — mesma tabela de /financeiro/precos/ — para exibição
    e cobrança de preços dinâmicos por estado, igual ao registro-civil.
    """
    tipo_cartorio = "imoveis"
    _product_slug = ""
    imagem_static = "img/certidao-de-nascimento.png"

    def _ctx(self, dados_ec, form):
        from products.services import get_state_prices_dict
        from products.models import Product
        ctx = super()._ctx(dados_ec, form)
        try:
            product = Product.objects.select_related('category').get(
                slug=self._product_slug, is_active=True
            )
            ctx["state_prices_json"] = json.dumps(get_state_prices_dict(product))
            ctx["product_base_price"] = str(product.price)
        except Product.DoesNotExist:
            ctx["state_prices_json"] = "{}"
            ctx["product_base_price"] = "0"
        return ctx


class BaseImovelVarianteDadosView(View):
    """
    Etapa 2 genérica para variantes do Registro de Imóveis.
    Usa ServiceStatePrice (mesma fonte de /financeiro/precos/) para calcular e
    cobrar preços por estado — padrão idêntico ao registro-civil.
    """
    title = ""
    form_class = None
    template_name = ""
    product_slug = ""
    step1_url = ""
    tipo_preco = ""          # identificador do tipo de certidão (ex: 'matricula')
    tipo_certidao_valor = "imovel"  # valor gravado em CartItem.tipo_certidao
    descricao_step2 = "Informe os dados do imóvel."
    date_fields = []
    date_field_ids = []

    def _get_cartorio(self, request):
        return request.session.get("certidao_cartorio")

    def _get_product(self):
        from products.models import Product
        try:
            return Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return None

    def _ctx(self, form, cartorio_data):
        from products.services import obter_preco_por_estado
        estado_uf = (cartorio_data or {}).get("estado_uf", "")
        preco = None
        if estado_uf:
            product = self._get_product()
            if product:
                preco = obter_preco_por_estado(product, estado_uf)
                if preco is None:
                    preco = product.price
        preco_display = None
        if preco is not None:
            preco_display = "R$ " + f"{preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return {
            "title": self.title,
            "form": form,
            "cartorio_data": cartorio_data,
            "step1_url": self.step1_url,
            "date_field_ids": mark_safe(json.dumps(self.date_field_ids)),
            "descricao_step2": self.descricao_step2,
            "preco_display": preco_display,
            "estado_uf": estado_uf,
        }

    def get(self, request):
        cartorio_data = self._get_cartorio(request)
        if not cartorio_data:
            messages.warning(request, "Por favor, preencha os dados do cartório primeiro.")
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
                if key in self.date_fields and hasattr(val, "strftime"):
                    dados[key] = val.strftime("%d/%m/%Y")
                else:
                    dados[key] = val or ""
            dados["tipo_certidao"] = self.tipo_preco
            request.session["certidao_dados"] = dados
            self._add_to_cart(request, cartorio_data, dados)
            cartorio_id = cartorio_data.get("cartorio_id")
            if cartorio_id:
                request.session["ordem_cartorio_id"] = cartorio_id
            return redirect("orders:checkout")
        return render(request, self.template_name, self._ctx(form, cartorio_data))

    def _add_to_cart(self, request, cartorio_data, dados):
        from products.models import State
        from products.services import obter_preco_por_estado
        from orders.models import Cart, CartItem
        product = self._get_product()
        if not product:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(
            dados.get("nome_completo") or dados.get("numero_matricula") or ""
        )[:200]
        item.requester_document = str(dados.get("cpf", ""))[:30]

        # Preço sempre recalculado do banco — nunca confia no frontend
        estado_uf = cartorio_data.get("estado_uf", "")
        item.tipo_certidao = self.tipo_certidao_valor
        if estado_uf:
            unit_price = obter_preco_por_estado(product, estado_uf)
            if unit_price is None:
                unit_price = product.price
            item.unit_price = unit_price
            state_obj = State.objects.filter(code=estado_uf).first()
            if state_obj:
                item.state = state_obj
        item.save()

        request.session["ordem_cidade"] = cartorio_data.get("cidade", "")
        request.session["ordem_cartorio_nome"] = cartorio_data.get("cartorio", "")


# ─── Certidão Negativa de Alienação Fiduciária ──────────────────────────────

class CertidaoAlienacaoFiduciariaView(BaseImovelVarianteView):
    title = "Certidão Negativa de Alienação Fiduciária — E-Registro Brasil"
    template_name = "servicos/imoveis/alienacao_fiduciaria_cartorio.html"
    dados_step_name = "pages:certidao_alienacao_fiduciaria_dados"
    _product_slug = "certidao-negativa-de-alienacao-fiduciaria"
    descricao_servico = (
        "Certidão que comprova a inexistência de alienação fiduciária registrada em "
        "nome do titular no Cartório de Registro de Imóveis."
    )


class CertidaoAlienacaoFiduciariaDadosView(BaseImovelVarianteDadosView):
    from .forms import CertidaoAlienacaoFiduciariaForm as _CertidaoAlienacaoFiduciariaForm
    title = "Certidão Negativa de Alienação Fiduciária — E-Registro Brasil"
    form_class = _CertidaoAlienacaoFiduciariaForm
    template_name = "servicos/imoveis/alienacao_fiduciaria_dados.html"
    product_slug = "certidao-negativa-de-alienacao-fiduciaria"
    step1_url = "pages:certidao_alienacao_fiduciaria"
    tipo_preco = "alienacao_fiduciaria"
    tipo_certidao_valor = "imovel_alienacao_fiduciaria"
    descricao_step2 = "Informe o nome e CPF do titular para pesquisa de alienação fiduciária."


# ─── Certidão de Matrícula Atualizada ───────────────────────────────────────

class CertidaoMatriculaAtualizadaView(BaseImovelVarianteView):
    title = "Certidão de Matrícula Atualizada — E-Registro Brasil"
    template_name = "servicos/imoveis/matricula_atualizada_cartorio.html"
    dados_step_name = "pages:certidao_matricula_atualizada_dados"
    _product_slug = "certidao-de-matricula-atualizada"
    descricao_servico = (
        "Certidão atualizada que reflete a situação jurídica atual do imóvel: "
        "titularidade, ônus, gravames e histórico completo de transações."
    )


class CertidaoMatriculaAtualizadaDadosView(BaseImovelVarianteDadosView):
    from .forms import CertidaoImovelMatriculaForm as _CertidaoImovelMatriculaForm
    title = "Certidão de Matrícula Atualizada — E-Registro Brasil"
    form_class = _CertidaoImovelMatriculaForm
    template_name = "servicos/imoveis/matricula_atualizada_dados.html"
    product_slug = "certidao-de-matricula-atualizada"
    step1_url = "pages:certidao_matricula_atualizada"
    tipo_preco = "matricula"
    tipo_certidao_valor = "imovel_matricula_atualizada"
    descricao_step2 = "Informe o número da matrícula do imóvel."


# ─── Certidão de Ônus Reais ──────────────────────────────────────────────────

class CertidaoOnusReaisView(BaseImovelVarianteView):
    title = "Certidão de Ônus Reais — E-Registro Brasil"
    template_name = "servicos/imoveis/onus_reais_cartorio.html"
    dados_step_name = "pages:certidao_onus_reais_dados"
    _product_slug = "certidao-de-onus-reais"
    descricao_servico = (
        "Certidão que lista todos os ônus, hipotecas, penhoras e gravames "
        "incidentes sobre o imóvel, incluindo cópia integral da matrícula."
    )


class CertidaoOnusReaisDadosView(BaseImovelVarianteDadosView):
    from .forms import CertidaoImovelInteiroTeorForm as _CertidaoImovelInteiroTeorForm
    title = "Certidão de Ônus Reais — E-Registro Brasil"
    form_class = _CertidaoImovelInteiroTeorForm
    template_name = "servicos/imoveis/onus_reais_dados.html"
    product_slug = "certidao-de-onus-reais"
    step1_url = "pages:certidao_onus_reais"
    tipo_preco = "inteiro_teor"
    tipo_certidao_valor = "imovel_onus_reais"
    descricao_step2 = "Informe o número da matrícula para a certidão de ônus reais."


# ─── Pesquisa de Bens ────────────────────────────────────────────────────────

class PesquisaBensView(BaseImovelVarianteView):
    title = "Pesquisa de Bens — E-Registro Brasil"
    template_name = "servicos/imoveis/pesquisa_bens_cartorio.html"
    dados_step_name = "pages:pesquisa_bens_dados"
    _product_slug = "pesquisa-de-bens"
    descricao_servico = (
        "Pesquisa de bens imóveis registrados em nome de pessoa física ou jurídica "
        "no Cartório de Registro de Imóveis."
    )

    def post(self, request):
        from .forms import PesquisaBensCartorioForm
        from registry.models import Registry
        dados_ec = _load_estados_cidades()
        form = PesquisaBensCartorioForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            estado_uf = cd['estado'].upper()
            estado_nome = dados_ec.get(estado_uf, {}).get('nome', estado_uf)
            todos = bool(cd.get('todos_cartorios', False))
            qtd_cartorios = 1
            if todos:
                # Quantidade recontada no servidor — nunca confia no frontend
                qtd_cartorios = Registry.objects.filter(
                    estado=estado_uf,
                    cidade__iexact=cd['cidade'],
                    ativo=True,
                    tipo_servico__contains=self.tipo_cartorio,
                ).count() or 1
            request.session['certidao_cartorio'] = {
                'estado_uf': estado_uf,
                'estado_nome': estado_nome,
                'cidade': cd['cidade'],
                'cartorio': cd['cartorio'],
                'cartorio_id': cd.get('cartorio_id'),
                'todos_cartorios': todos,
                'qtd_cartorios': qtd_cartorios,
            }
            return redirect(self.dados_step_name)
        return render(request, self.template_name, self._ctx(dados_ec, form))


class PesquisaBensDadosView(BaseImovelVarianteDadosView):
    from .forms import PesquisaBensImovelForm as _PesquisaBensImovelForm
    title = "Pesquisa de Bens — E-Registro Brasil"
    form_class = _PesquisaBensImovelForm
    template_name = "servicos/imoveis/pesquisa_bens_dados.html"
    product_slug = "pesquisa-de-bens"
    step1_url = "pages:pesquisa_bens"
    tipo_preco = "pesquisa_bens"
    tipo_certidao_valor = "imovel_pesquisa_bens"
    descricao_step2 = "Informe o nome e CPF do titular para pesquisa de bens imóveis registrados."

    @staticmethod
    def _qtd_cartorios(cartorio_data):
        try:
            return max(int((cartorio_data or {}).get("qtd_cartorios") or 1), 1)
        except (TypeError, ValueError):
            return 1

    def _ctx(self, form, cartorio_data):
        from products.services import obter_preco_por_estado
        ctx = super()._ctx(form, cartorio_data)
        qtd = self._qtd_cartorios(cartorio_data)
        ctx["qtd_cartorios"] = qtd
        if qtd > 1:
            estado_uf = (cartorio_data or {}).get("estado_uf", "")
            product = self._get_product()
            if estado_uf and product:
                preco = obter_preco_por_estado(product, estado_uf)
                if preco is None:
                    preco = product.price
                total = preco * qtd
                ctx["preco_display"] = "R$ " + f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return ctx

    def _add_to_cart(self, request, cartorio_data, dados):
        super()._add_to_cart(request, cartorio_data, dados)
        # Pesquisa em todos os cartórios da cidade: 1 busca por cartório
        from orders.models import CartItem
        product = self._get_product()
        if not product or not request.session.session_key:
            return
        CartItem.objects.filter(
            cart__session_key=request.session.session_key, product=product
        ).update(quantity=self._qtd_cartorios(cartorio_data))


# ===========================================================================
#  Certidão Negativa de Testamento
#  Pesquisa nacional de testamentos — preço fixo nacional (editável no painel)
#  Fluxo em 2 etapas: (1) nome do falecido + estado do óbito, (2) demais dados
# ===========================================================================

_TESTAMENTO_ETAPA1_SESSION_KEY = "testamento_etapa1"


class _BaseTestamentoView(View):
    title = "Certidão Negativa de Testamento — E-Registro Brasil"
    product_slug = "certidao-negativa-de-testamento"
    tipo_certidao_sessao = "busca_testamento"

    def _get_product(self):
        from products.models import Product
        try:
            return Product.objects.get(slug=self.product_slug, is_active=True)
        except Product.DoesNotExist:
            return None

    def _ctx(self, form, product=None):
        ctx = {
            "title": self.title,
            "form": form,
            "passos": _PASSOS,
        }
        if product:
            ctx["product"] = product
            price = product.price
            ctx['price_display'] = 'R$ {:,.2f}'.format(price).replace(',', 'X').replace('.', ',').replace('X', '.')
            ctx['show_fixed_price'] = True
        return ctx


class CertidaoNegativaTestamentoView(_BaseTestamentoView):
    """Etapa 1 — nome do falecido e local do registro do óbito."""
    template_name = "servicos/certidao_negativa_testamento.html"

    def get(self, request):
        initial = request.session.get(_TESTAMENTO_ETAPA1_SESSION_KEY) or {}
        form = CertidaoNegativaTestamentoEtapa1Form(initial=initial)
        return render(request, self.template_name, self._ctx(form, self._get_product()))

    def post(self, request):
        form = CertidaoNegativaTestamentoEtapa1Form(request.POST)
        if form.is_valid():
            request.session[_TESTAMENTO_ETAPA1_SESSION_KEY] = {
                'nome_falecido': form.cleaned_data['nome_falecido'],
                'estado_obito': form.cleaned_data['estado_obito'],
            }
            return redirect('pages:certidao_negativa_testamento_dados')
        return render(request, self.template_name, self._ctx(form, self._get_product()))


class CertidaoNegativaTestamentoDadosView(_BaseTestamentoView):
    """Etapa 2 — demais dados do falecido (CPF, datas, mãe, RG e órgão emissor)."""
    template_name = "servicos/certidao_negativa_testamento_dados.html"

    def _get_etapa1(self, request):
        return request.session.get(_TESTAMENTO_ETAPA1_SESSION_KEY)

    def _ctx(self, form, product=None, etapa1=None):
        ctx = super()._ctx(form, product)
        etapa1 = etapa1 or {}
        estado_uf = etapa1.get('estado_obito', '')
        ctx['etapa1'] = etapa1
        ctx['estado_obito_nome'] = dict(_ESTADOS_CHOICES).get(estado_uf, estado_uf)
        return ctx

    def get(self, request):
        etapa1 = self._get_etapa1(request)
        if not etapa1:
            messages.warning(request, 'Por favor, informe primeiro os dados do falecido.')
            return redirect('pages:certidao_negativa_testamento')
        form = CertidaoNegativaTestamentoForm()
        return render(request, self.template_name, self._ctx(form, self._get_product(), etapa1))

    def post(self, request):
        etapa1 = self._get_etapa1(request)
        if not etapa1:
            return redirect('pages:certidao_negativa_testamento')
        product = self._get_product()
        form = CertidaoNegativaTestamentoForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            dados = {k: v.strftime('%d/%m/%Y') if hasattr(v, 'strftime') else str(v) for k, v in cd.items()}
            dados['nome_falecido'] = etapa1.get('nome_falecido', '')
            dados['estado_obito'] = etapa1.get('estado_obito', '')
            dados['tipo_servico'] = self.product_slug
            request.session['certidao_dados'] = dados
            self._add_to_cart(request, dados, product)
            request.session.pop(_TESTAMENTO_ETAPA1_SESSION_KEY, None)
            return redirect('orders:checkout')
        return render(request, self.template_name, self._ctx(form, product, etapa1))

    def _add_to_cart(self, request, dados, product):
        from orders.models import Cart, CartItem
        if product is None:
            return
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = 1
        item.requester_name = str(dados.get('nome_falecido', ''))[:200]
        item.requester_document = str(dados.get('cpf_falecido', ''))[:30]
        item.unit_price = product.price
        item.tipo_certidao = self.tipo_certidao_sessao
        item.save()
        request.session['ordem_tipo_certidao'] = self.tipo_certidao_sessao
