from django.contrib import admin
from .models import BlogCategory, Post


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_published', 'published_at')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_published',)
    fieldsets = (
        ('Conteúdo', {'fields': ('title', 'slug', 'category', 'author', 'cover_image', 'excerpt', 'content')}),
        ('Publicação', {'fields': ('is_published', 'published_at')}),
        ('SEO', {'fields': ('meta_title', 'meta_description', 'meta_keywords'), 'classes': ('collapse',)}),
    )
