from django.contrib.sitemaps import Sitemap
from .models import Post


class BlogPostSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'

    def items(self):
        return Post.objects.filter(is_published=True).order_by('-published_at', '-created_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
