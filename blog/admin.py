from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import BlogCategory, Post


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count', 'description_preview')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    fields = ('name', 'slug', 'description')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _post_count=Count('posts', filter=Q(posts__is_published=True))
        )

    @admin.display(description='Artigos publicados', ordering='_post_count')
    def post_count(self, obj):
        return obj._post_count

    @admin.display(description='Descrição')
    def description_preview(self, obj):
        if obj.description:
            return obj.description[:80] + ('...' if len(obj.description) > 80 else '')
        return '—'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'author', 'is_published', 'is_featured',
        'views_count', 'published_at', 'cover_thumb',
    )
    list_filter = ('is_published', 'is_featured', 'category', 'author')
    list_editable = ('is_published', 'is_featured')
    search_fields = ('title', 'content', 'excerpt', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    readonly_fields = ('views_count', 'created_at', 'updated_at', 'cover_preview')
    ordering = ('-published_at', '-created_at')
    save_on_top = True

    fieldsets = (
        ('Conteúdo', {
            'fields': (
                'title', 'slug', 'category', 'author',
                'cover_image', 'cover_preview',
                'excerpt', 'content',
            ),
        }),
        ('Publicação', {
            'fields': ('is_published', 'is_featured', 'published_at'),
        }),
        ('Tags', {
            'fields': ('tags',),
            'description': 'Separe as tags com vírgulas. Ex: certidão, imóvel, registro civil',
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',),
        }),
        ('Métricas', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Capa')
    def cover_thumb(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="height:40px;width:60px;object-fit:cover;border-radius:6px;">',
                obj.cover_image.url,
            )
        return '—'

    @admin.display(description='Preview da Capa')
    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height:200px;max-width:400px;border-radius:10px;">',
                obj.cover_image.url,
            )
        return '—'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'category')

