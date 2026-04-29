import json
import os
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactForm


def _load_estados_cidades():
    json_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'estados_cidades.json')
    with open(json_path, encoding='utf-8') as f:
        return json.load(f)


class AboutView(TemplateView):
    template_name = 'pages/about.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Quem Somos — E-Registro Brasil'
        return ctx


class ContactView(FormView):
    template_name = 'pages/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('pages:contact')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Fale Conosco — E-Registro Brasil'
        return ctx

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            send_mail(
                subject=f"[Contato] {data['subject']}",
                message=f"Nome: {data['name']}\nE-mail: {data['email']}\n\n{data['message']}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass
        messages.success(self.request, 'Mensagem enviada com sucesso! Em breve entraremos em contato.')
        return super().form_valid(form)


class CertidaoNascimentoView(TemplateView):
    template_name = 'pages/certidao_nascimento.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Certidão de Nascimento 2ª Via — E-Registro Brasil'
        dados = _load_estados_cidades()
        ctx['estados'] = [
            {'uf': uf, 'nome': info['nome']}
            for uf, info in sorted(dados.items(), key=lambda x: x[1]['nome'])
        ]
        ctx['passos'] = [
            {'titulo': 'Preencha o formulário', 'descricao': 'Informe o estado, cidade e o cartório onde o registro foi realizado.'},
            {'titulo': 'Confirme o pedido', 'descricao': 'Revise os dados e conclua sua solicitação com segurança.'},
            {'titulo': 'Acompanhe o processo', 'descricao': 'Você receberá atualizações por e-mail durante todo o processo.'},
            {'titulo': 'Receba o documento', 'descricao': 'A certidão será enviada para o endereço cadastrado ou disponibilizada digitalmente.'},
        ]
        return ctx


class TermsView(TemplateView):
    template_name = 'pages/terms.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Termos de Uso — E-Registro Brasil'
        return ctx


class PrivacyView(TemplateView):
    template_name = 'pages/privacy.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Política de Privacidade — E-Registro Brasil'
        return ctx


class LegalView(TemplateView):
    template_name = 'pages/legal.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Ressalva Legal — E-Registro Brasil'
        return ctx
