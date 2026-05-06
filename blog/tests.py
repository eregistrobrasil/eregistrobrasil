from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import Post, BlogCategory


class BlogCategoryModelTest(TestCase):
    def test_slug_auto_generated(self):
        cat = BlogCategory.objects.create(name='Certidões de Nascimento')
        self.assertEqual(cat.slug, 'certidoes-de-nascimento')

    def test_str(self):
        cat = BlogCategory(name='Imóveis')
        self.assertEqual(str(cat), 'Imóveis')


class BlogPostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='autor', password='pass')
        self.cat = BlogCategory.objects.create(name='Geral')
        self.post = Post.objects.create(
            title='Artigo de Teste',
            content='<p>Conteúdo do artigo.</p> ' * 40,
            author=self.user,
            category=self.cat,
            is_published=True,
            published_at=timezone.now(),
            meta_keywords='certidão, registro, civil',
        )

    def test_slug_auto_generated(self):
        self.assertEqual(self.post.slug, 'artigo-de-teste')

    def test_str(self):
        self.assertIn('Artigo de Teste', str(self.post))

    def test_reading_time(self):
        self.assertGreaterEqual(self.post.reading_time, 1)

    def test_reading_time_short(self):
        post = Post.objects.create(
            title='Post Curto',
            content='<p>Apenas algumas palavras.</p>',
            author=self.user,
            is_published=True,
            published_at=timezone.now(),
        )
        self.assertEqual(post.reading_time, 1)

    def test_get_absolute_url(self):
        url = self.post.get_absolute_url()
        self.assertIn(self.post.slug, url)
        self.assertIn('/blog/', url)

    def test_meta_keywords_field(self):
        self.assertEqual(self.post.meta_keywords, 'certidão, registro, civil')


class BlogPublicViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='autor2', password='pass')
        self.cat = BlogCategory.objects.create(name='Notícias')
        self.published = Post.objects.create(
            title='Post Publicado',
            content='<p>Conteúdo visível.</p>',
            author=self.user,
            is_published=True,
            published_at=timezone.now(),
        )
        self.draft = Post.objects.create(
            title='Rascunho Secreto',
            content='<p>Não visível.</p>',
            author=self.user,
            is_published=False,
        )

    def test_list_view_loads(self):
        resp = self.client.get(reverse('blog:list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Post Publicado')

    def test_list_view_hides_drafts(self):
        resp = self.client.get(reverse('blog:list'))
        self.assertNotContains(resp, 'Rascunho Secreto')

    def test_detail_view_published(self):
        resp = self.client.get(reverse('blog:detail', kwargs={'slug': self.published.slug}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Post Publicado')

    def test_detail_view_draft_returns_404(self):
        resp = self.client.get(reverse('blog:detail', kwargs={'slug': self.draft.slug}))
        self.assertEqual(resp.status_code, 404)

    def test_list_search(self):
        resp = self.client.get(reverse('blog:list') + '?q=Publicado')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Post Publicado')

    def test_list_search_no_results(self):
        resp = self.client.get(reverse('blog:list') + '?q=inexistentexyz')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Nenhum artigo')

    def test_list_category_filter(self):
        resp = self.client.get(reverse('blog:list') + f'?categoria={self.cat.slug}')
        self.assertEqual(resp.status_code, 200)

    def test_detail_has_reading_time(self):
        resp = self.client.get(reverse('blog:detail', kwargs={'slug': self.published.slug}))
        self.assertContains(resp, 'min de leitura')

    def test_detail_sharing_buttons(self):
        resp = self.client.get(reverse('blog:detail', kwargs={'slug': self.published.slug}))
        self.assertContains(resp, 'wa.me')
        self.assertContains(resp, 'facebook.com')


class BlogDashboardAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(username='cliente', password='pass')
        self.staff_user = User.objects.create_user(username='operador', password='pass', is_staff=True)

    def test_anonymous_blocked(self):
        resp = self.client.get('/painel/blog/')
        self.assertIn(resp.status_code, [302, 403])

    def test_regular_user_blocked(self):
        self.client.login(username='cliente', password='pass')
        resp = self.client.get('/painel/blog/')
        self.assertIn(resp.status_code, [302, 403])

    def test_staff_can_access(self):
        self.client.login(username='operador', password='pass')
        resp = self.client.get('/painel/blog/')
        self.assertEqual(resp.status_code, 200)

    def test_staff_can_access_create(self):
        self.client.login(username='operador', password='pass')
        resp = self.client.get('/painel/blog/novo/')
        self.assertEqual(resp.status_code, 200)


class BlogSitemapTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='autor3', password='pass')
        Post.objects.create(
            title='Para Sitemap',
            content='Conteúdo.',
            author=self.user,
            is_published=True,
            published_at=timezone.now(),
        )

    def test_sitemap_loads(self):
        resp = self.client.get('/sitemap.xml')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('blog', resp.content.decode())

    def test_robots_txt_loads(self):
        resp = self.client.get('/robots.txt')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Sitemap', resp.content.decode())
        self.assertIn('Disallow: /painel/', resp.content.decode())
