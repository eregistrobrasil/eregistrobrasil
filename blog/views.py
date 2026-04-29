from django.views.generic import ListView, DetailView
from .models import Post, BlogCategory


class PostListView(ListView):
    model = Post
    template_name = 'blog/list.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        qs = Post.objects.filter(is_published=True).select_related('author', 'category')
        cat_slug = self.request.GET.get('categoria')
        if cat_slug:
            qs = qs.filter(category__slug=cat_slug)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['blog_categories'] = BlogCategory.objects.all()
        ctx['title'] = 'Blog — E-Registro Brasil'
        ctx['active_category'] = self.request.GET.get('categoria', '')
        return ctx


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects.filter(is_published=True).select_related('author', 'category')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['recent_posts'] = Post.objects.filter(
            is_published=True
        ).exclude(pk=self.object.pk)[:3]
        ctx['title'] = self.object.meta_title or self.object.title
        return ctx
