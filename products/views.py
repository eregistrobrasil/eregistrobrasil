from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Q
import json
from .models import Category, Product, ESTADOS_BR
from .services import get_state_prices_dict


class HomeView(ListView):
    model = Product
    template_name = 'home.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['featured_products'] = Product.objects.filter(
            is_active=True, is_featured=True
        ).select_related('category')[:6]
        ctx['categories'] = Category.objects.filter(is_active=True)
        ctx['title'] = 'Certidões Online — Rápido, Seguro e Fácil'
        return ctx


class CategoryDetailView(ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'], is_active=True)
        return Product.objects.filter(
            is_active=True, category=self.category
        ).select_related('category')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category'] = self.category
        ctx['title'] = f'{self.category.name} — Certidões Online'
        return ctx


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['related_products'] = Product.objects.filter(
            is_active=True, category=self.object.category
        ).exclude(pk=self.object.pk)[:4]
        ctx['title'] = self.object.meta_title or self.object.name
        ctx['estados'] = ESTADOS_BR
        # Preços por estado embutidos como JSON — evita chamadas AJAX individuais
        state_prices = get_state_prices_dict(self.object)
        ctx['state_prices_json'] = json.dumps(state_prices)
        ctx['has_state_prices'] = bool(state_prices)
        return ctx


class SearchView(ListView):
    model = Product
    template_name = 'products/search.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if query:
            return Product.objects.filter(is_active=True).filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query)
            ).select_related('category')
        return Product.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['query'] = self.request.GET.get('q', '')
        ctx['title'] = f'Busca: {ctx["query"]}'
        return ctx
