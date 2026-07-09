# Smoke test temporário da repaginação do painel (pode ser removido).
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from orders.models import Order, OrderStatusLog


class PainelSmokeTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username='smoke_admin', email='smoke@test.local', password='x',
            first_name='Smoke', last_name='Admin',
        )
        cls.order = Order.objects.create(
            status='novo',
            customer_name='Cliente Teste',
            customer_email='cliente@test.local',
            customer_cpf='123.456.789-00',
            customer_phone='(11) 99999-0000',
            tipo_certidao='nascimento',
            estado='SP',
            cidade='São Paulo',
            prioridade='alta',
            responsavel=cls.user,
            prazo_entrega=timezone.now() + timedelta(hours=48),
            sla_horas=72,
            total=199.90,
            categoria_painel='registro_civil',
        )
        OrderStatusLog.objects.create(
            order=cls.order, status_anterior='pending', status_novo='novo',
            usuario=cls.user, observacao='Smoke test',
        )

    def setUp(self):
        self.client.force_login(self.user)

    def _ok(self, url):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200, f'{url} -> {resp.status_code}')
        return resp

    def test_paginas_do_painel_renderizam(self):
        for url in [
            '/painel/',
            '/painel/kanban/',
            '/painel/pedidos/',
            '/painel/pedidos/?categoria=registro_civil',
            '/painel/pedidos/?q=teste&status=novo',
            '/painel/notificacoes/',
            '/painel/blog/',
            '/painel/blog/novo/',
            '/painel/cartorios/',
            '/painel/cartorios/novo/',
            '/painel/relatorios-ia/',
        ]:
            self._ok(url)

    def test_detalhe_do_pedido_renderiza(self):
        resp = self._ok(f'/painel/pedidos/{self.order.pk}/')
        self.assertContains(resp, self.order.short_id)
        self.assertContains(resp, 'Cliente Teste')

    def test_lista_renderiza_linha_do_pedido(self):
        resp = self._ok('/painel/pedidos/?categoria=registro_civil&tipo=nascimento')
        self.assertContains(resp, 'Cliente Teste')

    def test_documento_entregue_no_painel_aparece_na_area_do_cliente(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from documents.models import Document

        cliente = User.objects.create_user(username='cliente_smoke', password='x')
        pedido_cliente = Order.objects.create(
            user=cliente,
            status='novo',
            customer_name='Maria Cliente',
            customer_email='maria@test.local',
            customer_cpf='987.654.321-00',
            categoria_painel='registro_civil',
            total=150,
        )

        # Equipe faz upload da certidão pronta (documento_entregue) via painel.
        arquivo = SimpleUploadedFile('certidao.pdf', b'%PDF-1.4 conteudo falso', content_type='application/pdf')
        resp = self.client.post(
            f'/documentos/upload/{pedido_cliente.pk}/',
            {'tipo': 'documento_entregue', 'observacao': '', 'arquivos': [arquivo]},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Document.objects.filter(order=pedido_cliente, tipo='documento_entregue').exists())

        # Também envia um documento interno (RG), que não deve aparecer para o cliente.
        arquivo_rg = SimpleUploadedFile('rg.jpg', b'fake-image-bytes', content_type='image/jpeg')
        self.client.post(
            f'/documentos/upload/{pedido_cliente.pk}/',
            {'tipo': 'rg', 'observacao': '', 'arquivos': [arquivo_rg]},
            follow=True,
        )

        # Cliente acessa a área dele e deve ver só o documento entregue.
        self.client.logout()
        self.client.force_login(cliente)
        resp = self.client.get(f'/pedidos/pedido/{pedido_cliente.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'certidao.pdf')
        self.assertNotContains(resp, 'rg.jpg')
