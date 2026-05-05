from rest_framework import generics, permissions
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from .models import Category, TipoServico, Product, ServiceStatePrice, PrecoImovelEstado
from .serializers import CategorySerializer, TipoServicoSerializer, ServicoSerializer


class CategoriaListAPIView(generics.ListAPIView):
    """
    GET /api/categorias/
    Lista todas as categorias ativas, ordenadas por ordem.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by('order', 'name')


class TipoServicoListAPIView(generics.ListAPIView):
    """
    GET /api/tipos/
    Lista todos os tipos de serviço.
    """
    serializer_class = TipoServicoSerializer
    permission_classes = [permissions.AllowAny]
    queryset = TipoServico.objects.all().order_by('order', 'name')


class ServicoListAPIView(generics.ListAPIView):
    """
    GET /api/servicos/
    Lista serviços ativos com suporte a filtros:
      ?categoria=<slug>
      ?tipo=<slug>
      ?destaque=true
    """
    serializer_class = ServicoSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = (
            Product.objects
            .filter(is_active=True)
            .select_related('category', 'tipo')
            .order_by('category__order', 'order', 'name')
        )
        categoria = self.request.query_params.get('categoria')
        tipo = self.request.query_params.get('tipo')
        destaque = self.request.query_params.get('destaque')

        if categoria:
            qs = qs.filter(category__slug=categoria)
        if tipo:
            qs = qs.filter(tipo__slug=tipo)
        if destaque and destaque.lower() == 'true':
            qs = qs.filter(is_featured=True)

        return qs


class ServicoDetailAPIView(generics.RetrieveAPIView):
    """
    GET /api/servicos/<slug>/
    Detalhe de um serviço pelo slug.
    """
    serializer_class = ServicoSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category', 'tipo')


class ServicePriceByStateView(View):
    """
    GET /api/preco/?service=<slug>&estado=<UF>
    Retorna o preço do serviço para o estado solicitado.
    """

    def get(self, request):
        slug = request.GET.get('service', '').strip()
        estado_code = request.GET.get('estado', '').strip().upper()

        if not slug or not estado_code:
            return JsonResponse({'error': 'Parâmetros service e estado são obrigatórios.'}, status=400)

        service = get_object_or_404(Product, slug=slug, is_active=True)

        try:
            ssp = (
                ServiceStatePrice.objects
                .select_related('state')
                .get(service=service, state__code=estado_code, is_active=True)
            )
            return JsonResponse({
                'price': str(ssp.price),
                'promotional_price': str(ssp.promotional_price) if ssp.promotional_price else None,
                'display_price': str(ssp.display_price),
                'state_code': estado_code,
                'state_name': ssp.state.name,
            })
        except ServiceStatePrice.DoesNotExist:
            # Fallback para o preço base do produto
            return JsonResponse({
                'price': str(service.price),
                'promotional_price': str(service.original_price) if service.original_price else None,
                'display_price': str(service.price),
                'state_code': estado_code,
                'state_name': estado_code,
                'fallback': True,
            })


class ImovelPriceByStateView(View):
    """
    GET /api/preco-imovel/?tipo=<tipo_certidao>&estado=<UF>
    Retorna o preço da certidão de imóvel para o tipo e estado informados.
    Usado pelo frontend para exibição dinâmica — nunca é fonte de verdade
    para cobrança (a view de checkout relê do banco).
    """

    def get(self, request):
        tipo = request.GET.get('tipo', '').strip().lower()
        estado_code = request.GET.get('estado', '').strip().upper()

        if not tipo or not estado_code:
            return JsonResponse(
                {'error': 'Parâmetros tipo e estado são obrigatórios.'}, status=400
            )

        try:
            obj = (
                PrecoImovelEstado.objects
                .select_related('state')
                .get(tipo_certidao=tipo, state__code=estado_code, is_active=True)
            )
            return JsonResponse({
                'price': str(obj.price),
                'display_price': str(obj.price),
                'state_code': estado_code,
                'state_name': obj.state.name,
            })
        except PrecoImovelEstado.DoesNotExist:
            return JsonResponse({'error': 'Preço não encontrado.'}, status=404)
