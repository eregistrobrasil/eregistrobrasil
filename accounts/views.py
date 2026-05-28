from django.views.generic import CreateView, TemplateView, UpdateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import RegisterForm, LoginForm, ProfileForm


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Cadastro realizado com sucesso! Faça login para continuar.')
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Criar Conta'
        return ctx


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Entrar'
        return ctx


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.request.user.orders.all()
        ctx['title'] = 'Minha Conta'
        ctx['orders'] = qs.order_by('-created_at')[:10]
        ctx['total_pedidos'] = qs.count()
        ctx['pedidos_andamento'] = qs.filter(status__in=['pending', 'paid', 'processing']).count()
        ctx['pedidos_concluidos'] = qs.filter(status='completed').count()
        profile = getattr(self.request.user, 'profile', None)
        ctx['senha_temporaria'] = (
            profile
            and profile.senha_gerada_automaticamente
            and not profile.senha_alterada_pelo_usuario
        )
        return ctx


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:dashboard')

    def get_object(self):
        return self.request.user.profile

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['first_name'].initial = self.request.user.first_name
        form.fields['last_name'].initial = self.request.user.last_name
        form.fields['email'].initial = self.request.user.email
        return form

    def form_valid(self, form):
        user = self.request.user
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.save()
        messages.success(self.request, 'Perfil atualizado com sucesso!')
        return super().form_valid(form)


class ChangePasswordView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/change_password.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Alterar Senha'
        ctx['form'] = kwargs.get('form') or PasswordChangeForm(self.request.user)
        return ctx

    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            # Marca que a senha foi alterada pelo usuário
            profile = getattr(request.user, 'profile', None)
            if profile:
                profile.senha_alterada_pelo_usuario = True
                profile.senha_gerada_automaticamente = False
                profile.save(update_fields=['senha_alterada_pelo_usuario', 'senha_gerada_automaticamente'])
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('accounts:dashboard')
        return render(request, self.template_name, {
            'title': 'Alterar Senha',
            'form': form,
        })

