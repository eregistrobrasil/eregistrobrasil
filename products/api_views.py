from rest_framework import generics, permissions
from .models import Category, TipoServico, Product
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
