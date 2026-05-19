from django.views.generic import TemplateView, DetailView, ListView
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse

from products.models import Product
from .models import Cart, CartItem, Order, OrderItem, TIPO_CERTIDAO_PARA_CATEGORIA, PRODUTO_SLUG_PARA_TIPO
from .forms import CheckoutForm


def _get_or_create_cart(request):
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


class CartView(TemplateView):
    template_name = 'orders/cart.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cart = _get_or_create_cart(self.request)
        ctx['cart'] = cart
        ctx['cart_items'] = cart.items.select_related('product').all()
        ctx['title'] = 'Meu Carrinho'
        return ctx


class AddToCartView(View):
    def post(self, request, slug):
        from products.models import State
        from products.services import obter_preco_por_estado
        product = get_object_or_404(Product, slug=slug, is_active=True)
        cart = _get_or_create_cart(request)

        estado_code = request.POST.get('estado', '').strip().upper()

        # Segurança: o preço SEMPRE vem do banco, nunca do formulário
        unit_price = obter_preco_por_estado(product, estado_code) if estado_code else None
        state_obj = None
        if estado_code:
            state_obj = State.objects.filter(code=estado_code).first()

        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += 1
        if state_obj is not None:
            item.state = state_obj
        # unit_price None → get_total() usa product.price como fallback
        if unit_price is not None:
            item.unit_price = unit_price
        item.save()

        messages.success(request, f'"{product.name}" adicionado ao carrinho.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'count': cart.get_count(), 'message': 'Adicionado!'})
        return redirect('orders:cart')


class RemoveFromCartView(View):
    def post(self, request, item_id):
        item = get_object_or_404(CartItem, id=item_id, cart__session_key=request.session.session_key)
        item.delete()
        messages.info(request, 'Item removido do carrinho.')
        return redirect('orders:cart')


class UpdateCartView(View):
    def post(self, request, item_id):
        item = get_object_or_404(CartItem, id=item_id, cart__session_key=request.session.session_key)
        qty = int(request.POST.get('quantity', 1))
        if qty > 0:
            item.quantity = qty
            item.save()
        else:
            item.delete()
        return redirect('orders:cart')


class CheckoutView(View):
    template_name = 'orders/checkout.html'

    def get(self, request):
        cart = _get_or_create_cart(request)
        if not cart.items.exists():
            messages.warning(request, 'Seu carrinho está vazio.')
            return redirect('orders:cart')
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'customer_name': request.user.get_full_name(),
                'customer_email': request.user.email,
                'customer_cpf': getattr(request.user, 'profile', None) and request.user.profile.cpf or '',
                'customer_phone': getattr(request.user, 'profile', None) and request.user.profile.phone or '',
            }
        form = CheckoutForm(initial=initial)
        return self._render(request, form, cart)

    def post(self, request):
        cart = _get_or_create_cart(request)
        if not cart.items.exists():
            return redirect('orders:cart')
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.subtotal = cart.get_total()
            order.total = cart.get_total()
            order.save()

            # Recupera dados do formulário de certidão salvos na sessão
            certidao_dados = request.session.pop('certidao_dados', {})
            _LABEL_MAP = {
                'conjuge_1': 'Cônjuge 1',
                'conjuge_2': 'Cônjuge 2',
                'data_casamento': 'Data do Casamento',
                'nome_completo': 'Nome Completo',
                'nome_mae': 'Nome da Mãe',
                'nome_pai': 'Nome do Pai',
                'data_nascimento': 'Data de Nascimento',
                'data_obito': 'Data de Óbito',
                'numero_livro': 'Nº Livro',
                'numero_folha': 'Nº Folha',
                'numero_termo': 'Nº Termo',
                'cpf': 'CPF',
                'estado_nascimento': 'Estado de Nascimento',
                'cidade_nascimento': 'Cidade de Nascimento',
                'descricao': 'Descrição',
                'matricula': 'Matrícula',
                'numero_registro': 'Nº Registro',
                'logradouro': 'Logradouro',
                'complemento': 'Complemento',
                'bairro': 'Bairro',
                'cidade_imovel': 'Cidade do Imóvel',
            }

            cart_items = list(cart.items.select_related('product', 'state').all())
            for i, cart_item in enumerate(cart_items):
                effective_price = (
                    cart_item.unit_price
                    if cart_item.unit_price is not None
                    else cart_item.product.price
                )
                # Apenas o primeiro item recebe os dados da certidão da sessão
                additional_info = ''
                if i == 0 and certidao_dados:
                    lines = []
                    for key, val in certidao_dados.items():
                        if val:
                            label = _LABEL_MAP.get(key, key.replace('_', ' ').title())
                            lines.append(f'{label}: {val}')
                    additional_info = '\n'.join(lines)
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    price=effective_price,
                    quantity=cart_item.quantity,
                    requester_name=cart_item.requester_name,
                    requester_document=cart_item.requester_document,
                    additional_info=additional_info,
                )

            # ── Derivar tipo_certidao e categoria_painel ─────────────────────
            # Prioridade 1: CartItem.tipo_certidao (definido pelo fluxo de serviço)
            # Prioridade 2: sessão (compatibilidade com fluxo atual)
            # Prioridade 3: mapeamento pelo slug do produto (fallback seguro)
            update_fields = []

            tipo_certidao = (
                next((ci.tipo_certidao for ci in cart_items if ci.tipo_certidao), '')
                or request.session.pop('ordem_tipo_certidao', '')
                or PRODUTO_SLUG_PARA_TIPO.get(
                    cart_items[0].product.slug if cart_items else '', ''
                )
            )
            # Garante remoção da chave mesmo que não usada acima
            request.session.pop('ordem_tipo_certidao', None)

            if tipo_certidao and not order.tipo_certidao:
                order.tipo_certidao = tipo_certidao
                # categoria_painel é derivada em Order.save()
                update_fields.extend(['tipo_certidao', 'categoria_painel'])

            # ── Estado, cidade e cartório ─────────────────────────────────────
            if not order.estado and cart_items:
                first_state = next((ci.state.code for ci in cart_items if ci.state), None)
                if first_state:
                    order.estado = first_state
                    update_fields.append('estado')

            cidade = request.session.pop('ordem_cidade', '')
            if cidade and not order.cidade:
                order.cidade = cidade
                update_fields.append('cidade')

            cartorio_id = request.session.pop('ordem_cartorio_id', None)
            if cartorio_id and not order.cartorio_id:
                from registry.models import Registry
                cartorio_obj = Registry.objects.filter(pk=cartorio_id, ativo=True).first()
                if cartorio_obj:
                    order.cartorio = cartorio_obj
                    update_fields.append('cartorio')
            if update_fields:
                order.save(update_fields=update_fields)
            cart.items.all().delete()
            return redirect('payments:create', order_id=order.id)
        return self._render(request, form, cart)

    def _render(self, request, form, cart):
        from django.shortcuts import render
        return render(request, self.template_name, {
            'form': form,
            'cart': cart,
            'cart_items': cart.items.select_related('product', 'state').all(),
            'title': 'Finalizar Pedido',
        })


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Pedido #{self.object.short_id}'
        return ctx


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Meus Pedidos'
        return ctx
