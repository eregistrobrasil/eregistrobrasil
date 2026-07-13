from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Q, F, Count
from .models import Post, BlogCategory


def _sidebar_ctx():
    """Dados comuns da sidebar para todas as páginas do blog."""
    return {
        'sidebar_categories': (
            BlogCategory.objects
            .annotate(published_count=Count('posts', filter=Q(posts__is_published=True)))
            .filter(published_count__gt=0)
            .order_by('name')
        ),
        'sidebar_popular': (
            Post.objects
            .filter(is_published=True)
            .select_related('category')
            .order_by('-views_count')[:5]
        ),
        'sidebar_recent': (
            Post.objects
            .filter(is_published=True)
            .select_related('category')
            .order_by('-published_at', '-created_at')[:5]
        ),
    }


class PostListView(ListView):
    model = Post
    template_name = 'blog/list.html'
    context_object_name = 'posts'
    paginate_by = 8

    def get_queryset(self):
        qs = Post.objects.filter(is_published=True).select_related('author', 'category')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(excerpt__icontains=q)
                | Q(content__icontains=q)
                | Q(tags__icontains=q)
            )
        # Exclude the featured post from the main grid when no search
        if not q:
            featured = Post.objects.filter(is_published=True, is_featured=True).first()
            if featured:
                qs = qs.exclude(pk=featured.pk)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_sidebar_ctx())
        ctx['blog_categories'] = BlogCategory.objects.all()
        ctx['title'] = 'Blog — E-Registro Brasil LTDA'
        ctx['search_query'] = self.request.GET.get('q', '')
        ctx['active_category'] = ''
        ctx['meta_description'] = (
            'Artigos, guias e dicas sobre certidões, documentão e cartórios no Brasil. '
            'Blog E-Registro Brasil LTDA.'
        )
        if not ctx['search_query']:
            ctx['featured_post'] = (
                Post.objects
                .filter(is_published=True, is_featured=True)
                .select_related('author', 'category')
                .first()
            )
        else:
            ctx['featured_post'] = None
        return ctx


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        self.category = get_object_or_404(BlogCategory, slug=self.kwargs['slug'])
        return (
            Post.objects
            .filter(is_published=True, category=self.category)
            .select_related('author', 'category')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_sidebar_ctx())
        ctx['category'] = self.category
        ctx['blog_categories'] = BlogCategory.objects.all()
        ctx['active_category'] = self.category.slug
        ctx['title'] = f'{self.category.name} — Blog E-Registro Brasil LTDA'
        ctx['meta_description'] = (
            f'Artigos sobre {self.category.name} no Blog E-Registro Brasil LTDA. '
            'Guias completos, dicas e informações sobre certidões e cartórios.'
        )
        return ctx


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects.filter(is_published=True).select_related('author', 'category')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Incrementa contagem de visualizações de forma atômica
        Post.objects.filter(pk=self.object.pk).update(views_count=F('views_count') + 1)
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_sidebar_ctx())

        # Artigos relacionados: mesma categoria, excluindo o atual
        related_qs = (
            Post.objects
            .filter(is_published=True)
            .exclude(pk=self.object.pk)
            .select_related('author', 'category')
        )
        if self.object.category:
            by_cat = related_qs.filter(category=self.object.category)[:3]
            if by_cat.count() >= 3:
                ctx['related_posts'] = by_cat
            else:
                ctx['related_posts'] = related_qs.order_by('-published_at', '-created_at')[:3]
        else:
            ctx['related_posts'] = related_qs.order_by('-published_at', '-created_at')[:3]

        ctx['title'] = self.object.meta_title or self.object.title
        ctx['meta_description'] = self.object.meta_description or self.object.excerpt or ''
        ctx['meta_keywords'] = self.object.meta_keywords or ''
        return ctx

