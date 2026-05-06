from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.contrib import messages
from django.contrib.auth.models import User

from orders.models import Order, OrderStatusLog
from notifications.models import Notification


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/conta/login/?next={request.path}')
        if not (request.user.is_staff or hasattr(request.user, 'profile') and
                request.user.profile.tipo in ('admin', 'operador', 'financeiro')):
            return HttpResponse('Acesso negado.', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


@method_decorator(staff_required, name='dispatch')
class DashboardIndexView(View):
    template_name = 'dashboard/index.html'

    def _pode_ver_financeiro(self, user):
        if user.is_superuser:
            return True
        return hasattr(user, 'profile') and user.profile.tipo in ('admin', 'financeiro')

    def get(self, request):
        hoje = timezone.now().date()
        inicio_hoje = timezone.make_aware(timezone.datetime.combine(hoje, timezone.datetime.min.time()))

        pedidos_hoje = Order.objects.filter(created_at__gte=inicio_hoje)
        pedidos_ativos = Order.objects.exclude(status__in=('concluido', 'cancelado', 'refunded', 'completed'))
        pedidos_atrasados = [o for o in pedidos_ativos if o.esta_atrasado]
        concluidos_hoje = Order.objects.filter(data_conclusao__gte=inicio_hoje, status='concluido')

        ultimos_pedidos = Order.objects.select_related('responsavel').order_by('-created_at')[:10]

        ctx = {
            'title': 'Dashboard',
            'pedidos_hoje': pedidos_hoje.count(),
            'pedidos_ativos': pedidos_ativos.count(),
            'pedidos_atrasados': len(pedidos_atrasados),
            'concluidos_hoje': concluidos_hoje.count(),
            'ultimos_pedidos': ultimos_pedidos,
            'status_labels': dict(Order.STATUS_CHOICES),
            'pode_ver_financeiro': self._pode_ver_financeiro(request.user),
        }
        return render(request, self.template_name, ctx)


@method_decorator(staff_required, name='dispatch')
class KanbanView(View):
    template_name = 'dashboard/kanban.html'

    COLUNAS = [
        ('novo', 'Novo'),
        ('em_analise', 'Em Análise'),
        ('aguardando_documentos', 'Aguard. Docs'),
        ('em_processamento', 'Em Processamento'),
        ('em_cartorio', 'Em Cartório'),
        ('pronto_envio', 'Pronto p/ Envio'),
        ('enviado', 'Enviado'),
    ]

    def get(self, request):
        responsavel_id = request.GET.get('responsavel')
        tipo = request.GET.get('tipo')
        prioridade = request.GET.get('prioridade')

        qs = Order.objects.select_related('responsavel', 'cartorio').order_by(
            '-prioridade', 'prazo_entrega'
        )

        if responsavel_id:
            qs = qs.filter(responsavel_id=responsavel_id)
        if tipo:
            qs = qs.filter(tipo_certidao=tipo)
        if prioridade:
            qs = qs.filter(prioridade=prioridade)

        colunas = []
        for status_key, label in self.COLUNAS:
            pedidos = [o for o in qs if o.status == status_key]
            colunas.append({
                'status': status_key,
                'label': label,
                'pedidos': pedidos,
                'count': len(pedidos),
            })

        operadores = User.objects.filter(
            profile__tipo__in=('admin', 'operador')
        ).select_related('profile')

        ctx = {
            'title': 'Kanban de Pedidos',
            'colunas': colunas,
            'operadores': operadores,
            'tipos': Order.TIPO_CERTIDAO_CHOICES,
            'prioridades': Order.PRIORIDADE_CHOICES,
            'filtro_responsavel': responsavel_id,
            'filtro_tipo': tipo,
            'filtro_prioridade': prioridade,
        }
        return render(request, self.template_name, ctx)


@method_decorator(staff_required, name='dispatch')
class OrderOpsListView(View):
    template_name = 'dashboard/order_list.html'

    def get(self, request):
        qs = Order.objects.select_related('responsavel', 'cartorio').order_by('-created_at')

        status = request.GET.get('status')
        tipo = request.GET.get('tipo')
        estado = request.GET.get('estado')
        responsavel_id = request.GET.get('responsavel')
        prioridade = request.GET.get('prioridade')
        busca = request.GET.get('q', '').strip()
        data_de = request.GET.get('data_de')
        data_ate = request.GET.get('data_ate')

        if status:
            qs = qs.filter(status=status)
        if tipo:
            qs = qs.filter(tipo_certidao=tipo)
        if estado:
            qs = qs.filter(estado=estado)
        if responsavel_id:
            qs = qs.filter(responsavel_id=responsavel_id)
        if prioridade:
            qs = qs.filter(prioridade=prioridade)
        if busca:
            qs = qs.filter(
                Q(customer_name__icontains=busca) |
                Q(customer_cpf__icontains=busca) |
                Q(customer_email__icontains=busca) |
                Q(id__icontains=busca)
            )
        if data_de:
            qs = qs.filter(created_at__date__gte=data_de)
        if data_ate:
            qs = qs.filter(created_at__date__lte=data_ate)

        operadores = User.objects.filter(
            profile__tipo__in=('admin', 'operador')
        ).select_related('profile')

        ctx = {
            'title': 'Pedidos',
            'pedidos': qs,
            'total': qs.count(),
            'operadores': operadores,
            'status_choices': Order.STATUS_CHOICES,
            'tipo_choices': Order.TIPO_CERTIDAO_CHOICES,
            'prioridade_choices': Order.PRIORIDADE_CHOICES,
            'pode_ver_financeiro': (
                request.user.is_superuser or (
                    hasattr(request.user, 'profile') and
                    request.user.profile.tipo in ('admin', 'financeiro')
                )
            ),
            'filtros': {
                'status': status, 'tipo': tipo, 'estado': estado,
                'responsavel': responsavel_id, 'prioridade': prioridade,
                'q': busca, 'data_de': data_de, 'data_ate': data_ate,
            },
        }
        return render(request, self.template_name, ctx)


@method_decorator(staff_required, name='dispatch')
class OrderOpsDetailView(View):
    template_name = 'dashboard/order_detail.html'

    def get(self, request, pk):
        order = get_object_or_404(Order.objects.select_related(
            'responsavel', 'cartorio', 'user'
        ).prefetch_related('items', 'logs', 'documents', 'notifications'), pk=pk)

        operadores = User.objects.filter(
            profile__tipo__in=('admin', 'operador')
        ).select_related('profile')

        ctx = {
            'title': f'Pedido #{order.short_id}',
            'order': order,
            'logs': order.logs.select_related('usuario').order_by('-data'),
            'documentos': order.documents.all(),
            'operadores': operadores,
            'status_choices': Order.STATUS_CHOICES,
            'prioridade_choices': Order.PRIORIDADE_CHOICES,
        }
        return render(request, self.template_name, ctx)


@method_decorator(staff_required, name='dispatch')
class AlterarStatusView(View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        novo_status = request.POST.get('status')
        observacao = request.POST.get('observacao', '')

        status_validos = [s[0] for s in Order.STATUS_CHOICES]
        if novo_status not in status_validos:
            messages.error(request, 'Status inválido.')
            return redirect('dashboard:order_detail', pk=pk)

        order.registrar_log(novo_status, usuario=request.user, observacao=observacao)
        status_anterior = order.status
        order.status = novo_status

        if novo_status == 'enviado':
            order.data_envio = timezone.now()
        if novo_status in ('concluido', 'completed'):
            order.data_conclusao = timezone.now()

        order.save()

        # Notificar responsável se diferente do usuário atual
        if order.responsavel and order.responsavel != request.user:
            Notification.criar(
                usuario=order.responsavel,
                tipo='status_alterado',
                mensagem=f'Pedido #{order.short_id} teve status alterado para "{order.get_status_display()}".',
                order=order,
            )

        # Dispara email assíncrono para status relevantes
        if novo_status in ('novo', 'em_processamento', 'enviado', 'concluido', 'cancelado'):
            from notifications.tasks import enviar_email_status
            enviar_email_status.delay(str(order.pk), novo_status)

        # Resposta HTMX
        if request.headers.get('HX-Request'):
            return render(request, 'dashboard/htmx/status_badge.html', {'order': order})

        messages.success(request, f'Status atualizado para "{order.get_status_display()}".')
        return redirect('dashboard:order_detail', pk=pk)


@method_decorator(staff_required, name='dispatch')
class AtribuirResponsavelView(View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        responsavel_id = request.POST.get('responsavel_id')

        if responsavel_id:
            try:
                responsavel = User.objects.get(pk=responsavel_id)
                order.responsavel = responsavel
                order.save(update_fields=['responsavel'])
                Notification.criar(
                    usuario=responsavel,
                    tipo='novo_pedido',
                    mensagem=f'Pedido #{order.short_id} foi atribuído a você.',
                    order=order,
                )
                messages.success(request, f'Pedido atribuído a {responsavel.get_full_name() or responsavel.username}.')
            except User.DoesNotExist:
                messages.error(request, 'Usuário não encontrado.')
        else:
            order.responsavel = None
            order.save(update_fields=['responsavel'])
            messages.success(request, 'Responsável removido.')

        if request.headers.get('HX-Request'):
            return render(request, 'dashboard/htmx/responsavel_badge.html', {'order': order})

        return redirect('dashboard:order_detail', pk=pk)


@method_decorator(login_required, name='dispatch')
class NotificacoesView(View):
    def get(self, request):
        notifs = Notification.objects.filter(
            usuario=request.user
        ).select_related('order').order_by('-data')[:50]
        Notification.objects.filter(usuario=request.user, lida=False).update(lida=True)
        return render(request, 'dashboard/notificacoes.html', {
            'title': 'Notificações',
            'notificacoes': notifs,
        })


@method_decorator(staff_required, name='dispatch')
class KanbanMoverView(View):
    def post(self, request):
        import json
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            novo_status = data.get('status')
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'ok': False, 'error': 'Dados inválidos'}, status=400)

        order = get_object_or_404(Order, pk=order_id)
        status_validos = [s[0] for s in Order.STATUS_CHOICES]
        if novo_status not in status_validos:
            return JsonResponse({'ok': False, 'error': 'Status inválido'}, status=400)

        order.registrar_log(novo_status, usuario=request.user, observacao='Movido via Kanban')
        order.status = novo_status
        if novo_status == 'enviado':
            order.data_envio = timezone.now()
        if novo_status in ('concluido', 'completed'):
            order.data_conclusao = timezone.now()
        order.save()

        if novo_status in ('novo', 'em_processamento', 'enviado', 'concluido', 'cancelado'):
            from notifications.tasks import enviar_email_status
            enviar_email_status.delay(str(order.pk), novo_status)

        return JsonResponse({'ok': True, 'status': order.get_status_display()})


# ─────────────────────────────────────────────
#  Blog — Painel Administrativo
# ─────────────────────────────────────────────

import html
import re as _re
from blog.models import Post, BlogCategory


def _sanitize_html(content):
    """Remove scripts e atributos perigosos do HTML do editor."""
    # Remove tags <script> e <iframe>
    content = _re.sub(r'<script[^>]*>.*?</script>', '', content, flags=_re.IGNORECASE | _re.DOTALL)
    content = _re.sub(r'<iframe[^>]*>.*?</iframe>', '', content, flags=_re.IGNORECASE | _re.DOTALL)
    # Remove atributos on* (onclick, onload, etc.)
    content = _re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=_re.IGNORECASE)
    content = _re.sub(r'\s+on\w+\s*=\s*[^\s>]+', '', content, flags=_re.IGNORECASE)
    # Remove javascript: em href/src
    content = _re.sub(r'(href|src)\s*=\s*["\']?\s*javascript:[^"\'>\s]*["\']?', '', content, flags=_re.IGNORECASE)
    return content


@method_decorator(staff_required, name='dispatch')
class BlogListView(View):
    template_name = 'dashboard/blog_list.html'

    def get(self, request):
        q = request.GET.get('q', '').strip()
        status = request.GET.get('status', '')
        qs = Post.objects.select_related('author', 'category').order_by('-created_at')
        if q:
            qs = qs.filter(title__icontains=q)
        if status == 'publicado':
            qs = qs.filter(is_published=True)
        elif status == 'rascunho':
            qs = qs.filter(is_published=False)
        return render(request, self.template_name, {
            'title': 'Blog',
            'posts': qs,
            'total': qs.count(),
            'q': q,
            'status_filter': status,
        })


@method_decorator(staff_required, name='dispatch')
class BlogCreateView(View):
    template_name = 'dashboard/blog_form.html'

    def get(self, request):
        categories = BlogCategory.objects.all()
        return render(request, self.template_name, {
            'title': 'Novo Artigo',
            'categories': categories,
            'post': None,
        })

    def post(self, request):
        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip()
        content = _sanitize_html(request.POST.get('content', ''))
        excerpt = request.POST.get('excerpt', '').strip()
        author_id = request.POST.get('author_id') or request.user.pk
        category_id = request.POST.get('category_id') or None
        is_published = request.POST.get('is_published') == '1'
        meta_title = request.POST.get('meta_title', '').strip()
        meta_description = request.POST.get('meta_description', '').strip()
        meta_keywords = request.POST.get('meta_keywords', '').strip()

        if not title or not content:
            messages.error(request, 'Título e conteúdo são obrigatórios.')
            return redirect('dashboard:blog_create')

        post = Post(
            title=title,
            content=content,
            excerpt=excerpt,
            author_id=author_id,
            is_published=is_published,
            meta_title=meta_title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
        )
        if slug:
            post.slug = slug
        if category_id:
            post.category_id = category_id
        if is_published and not post.published_at:
            post.published_at = timezone.now()
        if request.FILES.get('cover_image'):
            post.cover_image = request.FILES['cover_image']
        post.save()
        messages.success(request, 'Artigo criado com sucesso!')
        return redirect('dashboard:blog_list')


@method_decorator(staff_required, name='dispatch')
class BlogEditView(View):
    template_name = 'dashboard/blog_form.html'

    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        categories = BlogCategory.objects.all()
        authors = User.objects.filter(is_staff=True).order_by('first_name', 'username')
        return render(request, self.template_name, {
            'title': f'Editar: {post.title}',
            'post': post,
            'categories': categories,
            'authors': authors,
        })

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip()
        content = _sanitize_html(request.POST.get('content', ''))
        excerpt = request.POST.get('excerpt', '').strip()
        author_id = request.POST.get('author_id') or post.author_id
        category_id = request.POST.get('category_id') or None
        is_published = request.POST.get('is_published') == '1'
        meta_title = request.POST.get('meta_title', '').strip()
        meta_description = request.POST.get('meta_description', '').strip()
        meta_keywords = request.POST.get('meta_keywords', '').strip()

        if not title or not content:
            messages.error(request, 'Título e conteúdo são obrigatórios.')
            return redirect('dashboard:blog_edit', pk=pk)

        post.title = title
        if slug:
            post.slug = slug
        post.content = content
        post.excerpt = excerpt
        post.author_id = author_id
        post.category_id = category_id
        post.is_published = is_published
        post.meta_title = meta_title
        post.meta_description = meta_description
        post.meta_keywords = meta_keywords
        if is_published and not post.published_at:
            post.published_at = timezone.now()
        if request.FILES.get('cover_image'):
            post.cover_image = request.FILES['cover_image']
        post.save()
        messages.success(request, 'Artigo atualizado com sucesso!')
        return redirect('dashboard:blog_list')


@method_decorator(staff_required, name='dispatch')
class BlogDeleteView(View):
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        post.delete()
        messages.success(request, 'Artigo excluído com sucesso.')
        return redirect('dashboard:blog_list')


@method_decorator(staff_required, name='dispatch')
class BlogTogglePublishView(View):
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        post.is_published = not post.is_published
        if post.is_published and not post.published_at:
            post.published_at = timezone.now()
        post.save(update_fields=['is_published', 'published_at'])
        label = 'publicado' if post.is_published else 'despublicado'
        messages.success(request, f'Artigo {label} com sucesso.')
        return redirect('dashboard:blog_list')
