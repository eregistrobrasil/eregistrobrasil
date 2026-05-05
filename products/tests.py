"""
Testes para o sistema de preços por estado da Certidão de Imóvel.
Cobre: lookup correto, tipo inválido, estado inexistente, escalabilidade.
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from products.models import State, PrecoImovelEstado
from products.services import obter_preco_imovel, get_imovel_prices_dict


class PrecoImovelEstadoModelTest(TestCase):
    """Testes no nível do model PrecoImovelEstado."""

    @classmethod
    def setUpTestData(cls):
        cls.state_ba = State.objects.create(code='BA', name='Bahia')
        cls.state_sp = State.objects.create(code='SP', name='São Paulo')
        PrecoImovelEstado.objects.create(
            tipo_certidao='matricula', state=cls.state_ba, price=Decimal('249.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='matricula', state=cls.state_sp, price=Decimal('199.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='inteiro_teor', state=cls.state_ba, price=Decimal('274.89')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='inteiro_teor', state=cls.state_sp, price=Decimal('217.90')
        )
        # Tipo diferente, mesmo estado — permitido, sem conflito de unicidade
        cls.state_ac = State.objects.create(code='AC', name='Acre')
        PrecoImovelEstado.objects.create(
            tipo_certidao='matricula', state=cls.state_ac, price=Decimal('999.00'),
            is_active=False,
        )

    def test_str_representation(self):
        obj = PrecoImovelEstado.objects.get(tipo_certidao='matricula', state=self.state_ba)
        self.assertIn('matricula', str(obj))
        self.assertIn('BA', str(obj))

    def test_unique_together_enforced(self):
        from django.db import IntegrityError
        with self.assertRaises(Exception):
            PrecoImovelEstado.objects.create(
                tipo_certidao='matricula', state=self.state_ba, price=Decimal('1.00')
            )


class ObterPrecoImovelTest(TestCase):
    """Testes para a função obter_preco_imovel()."""

    @classmethod
    def setUpTestData(cls):
        cls.state_ba = State.objects.create(code='BA', name='Bahia')
        cls.state_rn = State.objects.create(code='RN', name='Rio Grande do Norte')
        PrecoImovelEstado.objects.create(
            tipo_certidao='matricula', state=cls.state_ba, price=Decimal('249.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='inteiro_teor', state=cls.state_ba, price=Decimal('274.89')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='inteiro_teor', state=cls.state_rn, price=Decimal('637.67')
        )

    # ── Casos de sucesso ──────────────────────────────────────────────────────

    def test_matricula_ba(self):
        preco = obter_preco_imovel('matricula', 'BA')
        self.assertEqual(preco, Decimal('249.90'))

    def test_inteiro_teor_ba(self):
        preco = obter_preco_imovel('inteiro_teor', 'BA')
        self.assertEqual(preco, Decimal('274.89'))

    def test_inteiro_teor_rn_valor_especifico(self):
        """RN tem o maior preço de Inteiro Teor: R$ 637,67."""
        preco = obter_preco_imovel('inteiro_teor', 'RN')
        self.assertEqual(preco, Decimal('637.67'))

    def test_case_insensitive_tipo(self):
        """Tipo em maiúsculas deve ser normalizado."""
        preco = obter_preco_imovel('INTEIRO_TEOR', 'BA')
        self.assertEqual(preco, Decimal('274.89'))

    def test_case_insensitive_estado(self):
        """UF em minúsculas deve ser normalizada."""
        preco = obter_preco_imovel('matricula', 'ba')
        self.assertEqual(preco, Decimal('249.90'))

    # ── Casos de erro / fallback ──────────────────────────────────────────────

    def test_tipo_invalido_retorna_none(self):
        preco = obter_preco_imovel('tipo_inexistente', 'BA')
        self.assertIsNone(preco)

    def test_estado_invalido_retorna_none(self):
        preco = obter_preco_imovel('matricula', 'XX')
        self.assertIsNone(preco)

    def test_estado_vazio_retorna_none(self):
        preco = obter_preco_imovel('matricula', '')
        self.assertIsNone(preco)

    def test_tipo_vazio_retorna_none(self):
        preco = obter_preco_imovel('', 'BA')
        self.assertIsNone(preco)

    def test_estado_sem_preco_cadastrado_retorna_none(self):
        """Estado válido mas sem preço para esse tipo."""
        preco = obter_preco_imovel('inteiro_teor', 'SP')  # não cadastrado no setUp
        self.assertIsNone(preco)


class GetImovelPricesDictTest(TestCase):
    """Testes para get_imovel_prices_dict()."""

    @classmethod
    def setUpTestData(cls):
        ba = State.objects.create(code='BA', name='Bahia')
        sp = State.objects.create(code='SP', name='São Paulo')
        PrecoImovelEstado.objects.create(
            tipo_certidao='matricula', state=ba, price=Decimal('249.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='matricula', state=sp, price=Decimal('199.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='inteiro_teor', state=ba, price=Decimal('274.89'),
            is_active=False,  # inativo — não deve entrar no dict
        )

    def test_retorna_dict_de_strings(self):
        d = get_imovel_prices_dict('matricula')
        self.assertIsInstance(d, dict)
        for k, v in d.items():
            self.assertIsInstance(k, str)
            self.assertIsInstance(v, str)

    def test_somente_ativos(self):
        d = get_imovel_prices_dict('inteiro_teor')
        self.assertNotIn('BA', d)  # inativo

    def test_tipo_sem_registros_retorna_vazio(self):
        d = get_imovel_prices_dict('vintenaria')
        self.assertEqual(d, {})

    def test_matricula_contém_dois_estados(self):
        d = get_imovel_prices_dict('matricula')
        self.assertIn('BA', d)
        self.assertIn('SP', d)
        self.assertEqual(d['BA'], '249.90')
        self.assertEqual(d['SP'], '199.90')


class ImovelPriceAPITest(TestCase):
    """Testes para GET /api/preco-imovel/?tipo=&estado="""

    @classmethod
    def setUpTestData(cls):
        state = State.objects.create(code='BA', name='Bahia')
        PrecoImovelEstado.objects.create(
            tipo_certidao='inteiro_teor', state=state, price=Decimal('274.89')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='matricula', state=state, price=Decimal('249.90')
        )

    def setUp(self):
        self.client = Client()

    def test_inteiro_teor_ba(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'inteiro_teor', 'estado': 'BA'})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['display_price'], '274.89')
        self.assertEqual(data['state_code'], 'BA')

    def test_matricula_ba(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'matricula', 'estado': 'BA'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '249.90')

    def test_tipo_invalido_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'invalido', 'estado': 'BA'})
        self.assertEqual(r.status_code, 404)

    def test_estado_invalido_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'matricula', 'estado': 'XX'})
        self.assertEqual(r.status_code, 404)

    def test_parametros_ausentes_retorna_400(self):
        r = self.client.get('/api/preco-imovel/')
        self.assertEqual(r.status_code, 400)

    def test_somente_tipo_retorna_400(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'matricula'})
        self.assertEqual(r.status_code, 400)


class VintenariaPrecoTest(TestCase):
    """Testes de preço para Vintenária."""

    @classmethod
    def setUpTestData(cls):
        cls.state_ba = State.objects.create(code='BA', name='Bahia')
        cls.state_sp = State.objects.create(code='SP', name='São Paulo')
        cls.state_rn = State.objects.create(code='RN', name='Rio Grande do Norte')
        cls.state_rr = State.objects.create(code='RR', name='Roraima')
        PrecoImovelEstado.objects.create(
            tipo_certidao='vintenaria', state=cls.state_ba, price=Decimal('274.89')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='vintenaria', state=cls.state_sp, price=Decimal('229.95')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='vintenaria', state=cls.state_rn, price=Decimal('379.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='vintenaria', state=cls.state_rr, price=Decimal('119.90')
        )

    # ── obter_preco_imovel ────────────────────────────────────────────────────

    def test_vintenaria_ba(self):
        self.assertEqual(obter_preco_imovel('vintenaria', 'BA'), Decimal('274.89'))

    def test_vintenaria_sp(self):
        self.assertEqual(obter_preco_imovel('vintenaria', 'SP'), Decimal('229.95'))

    def test_vintenaria_rn_maior_preco(self):
        """RN tem o maior preço de Vintenária: R$ 379,90."""
        self.assertEqual(obter_preco_imovel('vintenaria', 'RN'), Decimal('379.90'))

    def test_vintenaria_rr_menor_preco(self):
        """RR tem o menor preço de Vintenária: R$ 119,90."""
        self.assertEqual(obter_preco_imovel('vintenaria', 'RR'), Decimal('119.90'))

    def test_vintenaria_estado_invalido_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('vintenaria', 'ZZ'))

    def test_vintenaria_tipo_inexistente_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('tipo_invalido', 'BA'))

    # ── get_imovel_prices_dict ────────────────────────────────────────────────

    def test_dict_vintenaria_contem_quatro_estados(self):
        d = get_imovel_prices_dict('vintenaria')
        self.assertIn('BA', d)
        self.assertIn('SP', d)
        self.assertIn('RN', d)
        self.assertIn('RR', d)

    def test_dict_vintenaria_ba_valor_correto(self):
        d = get_imovel_prices_dict('vintenaria')
        self.assertEqual(d['BA'], '274.89')

    def test_dict_vintenaria_sp_valor_correto(self):
        d = get_imovel_prices_dict('vintenaria')
        self.assertEqual(d['SP'], '229.95')

    # ── API /api/preco-imovel/ ────────────────────────────────────────────────

    def test_api_vintenaria_ba(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'vintenaria', 'estado': 'BA'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '274.89')

    def test_api_vintenaria_sp(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'vintenaria', 'estado': 'SP'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '229.95')

    def test_api_vintenaria_estado_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'vintenaria', 'estado': 'XX'})
        self.assertEqual(r.status_code, 404)

    def test_api_tipo_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'tipo_qualquer', 'estado': 'BA'})
        self.assertEqual(r.status_code, 404)


class TranscricaoPrecoTest(TestCase):
    """Testes de preço para Transcrição."""

    @classmethod
    def setUpTestData(cls):
        cls.state_ba = State.objects.create(code='BA', name='Bahia')
        cls.state_mg = State.objects.create(code='MG', name='Minas Gerais')
        cls.state_ap = State.objects.create(code='AP', name='Amapá')
        cls.state_rr = State.objects.create(code='RR', name='Roraima')
        PrecoImovelEstado.objects.create(
            tipo_certidao='transcricao', state=cls.state_ba, price=Decimal('249.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='transcricao', state=cls.state_mg, price=Decimal('109.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='transcricao', state=cls.state_ap, price=Decimal('699.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='transcricao', state=cls.state_rr, price=Decimal('119.90')
        )

    # ── obter_preco_imovel ────────────────────────────────────────────────────

    def test_transcricao_ba(self):
        self.assertEqual(obter_preco_imovel('transcricao', 'BA'), Decimal('249.90'))

    def test_transcricao_mg_menor_preco_entre_tabelados(self):
        """MG tem o menor preço de Transcrição: R$ 109,90."""
        self.assertEqual(obter_preco_imovel('transcricao', 'MG'), Decimal('109.90'))

    def test_transcricao_ap_maior_preco(self):
        """AP tem o maior preço de Transcrição: R$ 699,90."""
        self.assertEqual(obter_preco_imovel('transcricao', 'AP'), Decimal('699.90'))

    def test_transcricao_rr(self):
        self.assertEqual(obter_preco_imovel('transcricao', 'RR'), Decimal('119.90'))

    def test_transcricao_estado_invalido_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('transcricao', 'ZZ'))

    def test_transcricao_tipo_inexistente_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('tipo_invalido', 'BA'))

    def test_transcricao_estado_sem_preco_retorna_none(self):
        """Estado válido mas sem preço de transcrição cadastrado."""
        self.assertIsNone(obter_preco_imovel('transcricao', 'SP'))

    # ── get_imovel_prices_dict ────────────────────────────────────────────────

    def test_dict_transcricao_contem_quatro_estados(self):
        d = get_imovel_prices_dict('transcricao')
        self.assertIn('BA', d)
        self.assertIn('MG', d)
        self.assertIn('AP', d)
        self.assertIn('RR', d)

    def test_dict_transcricao_ba_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('transcricao')['BA'], '249.90')

    def test_dict_transcricao_ap_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('transcricao')['AP'], '699.90')

    # ── API /api/preco-imovel/ ────────────────────────────────────────────────

    def test_api_transcricao_ba(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'transcricao', 'estado': 'BA'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '249.90')

    def test_api_transcricao_mg(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'transcricao', 'estado': 'MG'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '109.90')

    def test_api_transcricao_ap(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'transcricao', 'estado': 'AP'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '699.90')

    def test_api_transcricao_estado_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'transcricao', 'estado': 'XX'})
        self.assertEqual(r.status_code, 404)

    def test_api_tipo_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'tipo_qualquer', 'estado': 'BA'})
        self.assertEqual(r.status_code, 404)


class DocArquivadoPrecoTest(TestCase):
    """Testes de preço para Documento Arquivado (chave: doc_arquivado)."""

    @classmethod
    def setUpTestData(cls):
        cls.state_ba = State.objects.create(code='BA', name='Bahia')
        cls.state_ce = State.objects.create(code='CE', name='Ceará')
        cls.state_mg = State.objects.create(code='MG', name='Minas Gerais')
        cls.state_ac = State.objects.create(code='AC', name='Acre')
        PrecoImovelEstado.objects.create(
            tipo_certidao='doc_arquivado', state=cls.state_ba, price=Decimal('699.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='doc_arquivado', state=cls.state_ce, price=Decimal('699.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='doc_arquivado', state=cls.state_mg, price=Decimal('229.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='doc_arquivado', state=cls.state_ac, price=Decimal('160.65')
        )

    # ── obter_preco_imovel ────────────────────────────────────────────────────

    def test_doc_arquivado_ba(self):
        self.assertEqual(obter_preco_imovel('doc_arquivado', 'BA'), Decimal('699.90'))

    def test_doc_arquivado_ce(self):
        self.assertEqual(obter_preco_imovel('doc_arquivado', 'CE'), Decimal('699.90'))

    def test_doc_arquivado_mg(self):
        self.assertEqual(obter_preco_imovel('doc_arquivado', 'MG'), Decimal('229.90'))

    def test_doc_arquivado_ac_menor_preco(self):
        """AC tem o menor preço de Doc. Arquivado: R$ 160,65."""
        self.assertEqual(obter_preco_imovel('doc_arquivado', 'AC'), Decimal('160.65'))

    def test_doc_arquivado_estado_invalido_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('doc_arquivado', 'ZZ'))

    def test_doc_arquivado_tipo_inexistente_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('tipo_invalido', 'BA'))

    def test_doc_arquivado_estado_sem_preco_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('doc_arquivado', 'SP'))

    # ── get_imovel_prices_dict ────────────────────────────────────────────────

    def test_dict_doc_arquivado_contem_estados(self):
        d = get_imovel_prices_dict('doc_arquivado')
        for uf in ('BA', 'CE', 'MG', 'AC'):
            self.assertIn(uf, d)

    def test_dict_doc_arquivado_ba_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('doc_arquivado')['BA'], '699.90')

    def test_dict_doc_arquivado_ac_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('doc_arquivado')['AC'], '160.65')

    # ── API /api/preco-imovel/ ────────────────────────────────────────────────

    def test_api_doc_arquivado_ba(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'doc_arquivado', 'estado': 'BA'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '699.90')

    def test_api_doc_arquivado_ce(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'doc_arquivado', 'estado': 'CE'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '699.90')

    def test_api_doc_arquivado_mg(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'doc_arquivado', 'estado': 'MG'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '229.90')

    def test_api_estado_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'doc_arquivado', 'estado': 'XX'})
        self.assertEqual(r.status_code, 404)

    def test_api_tipo_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'tipo_qualquer', 'estado': 'BA'})
        self.assertEqual(r.status_code, 404)


class PactoAntinupcialPrecoTest(TestCase):
    """Testes de preço para Pacto Antinupcial (chave: pacto_antinupcial)."""

    @classmethod
    def setUpTestData(cls):
        cls.state_ba = State.objects.create(code='BA', name='Bahia')
        cls.state_rj = State.objects.create(code='RJ', name='Rio de Janeiro')
        cls.state_pi = State.objects.create(code='PI', name='Piauí')
        cls.state_ac = State.objects.create(code='AC', name='Acre')
        cls.state_rn = State.objects.create(code='RN', name='Rio Grande do Norte')
        PrecoImovelEstado.objects.create(
            tipo_certidao='pacto_antinupcial', state=cls.state_ba, price=Decimal('699.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='pacto_antinupcial', state=cls.state_rj, price=Decimal('259.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='pacto_antinupcial', state=cls.state_pi, price=Decimal('192.08')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='pacto_antinupcial', state=cls.state_ac, price=Decimal('160.65')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='pacto_antinupcial', state=cls.state_rn, price=Decimal('699.90')
        )

    # ── obter_preco_imovel ────────────────────────────────────────────────────

    def test_pacto_antinupcial_ba(self):
        self.assertEqual(obter_preco_imovel('pacto_antinupcial', 'BA'), Decimal('699.90'))

    def test_pacto_antinupcial_rj(self):
        self.assertEqual(obter_preco_imovel('pacto_antinupcial', 'RJ'), Decimal('259.90'))

    def test_pacto_antinupcial_pi(self):
        """PI tem preço fracionado: R$ 192,08."""
        self.assertEqual(obter_preco_imovel('pacto_antinupcial', 'PI'), Decimal('192.08'))

    def test_pacto_antinupcial_ac_menor_preco(self):
        """AC tem o menor preço de Pacto Antinupcial: R$ 160,65."""
        self.assertEqual(obter_preco_imovel('pacto_antinupcial', 'AC'), Decimal('160.65'))

    def test_pacto_antinupcial_rn_maior_preco(self):
        """RN tem o maior preço de Pacto Antinupcial: R$ 699,90."""
        self.assertEqual(obter_preco_imovel('pacto_antinupcial', 'RN'), Decimal('699.90'))

    def test_pacto_antinupcial_estado_invalido_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('pacto_antinupcial', 'ZZ'))

    def test_pacto_antinupcial_tipo_inexistente_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('tipo_invalido', 'BA'))

    def test_pacto_antinupcial_estado_sem_preco_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('pacto_antinupcial', 'SP'))

    # ── get_imovel_prices_dict ────────────────────────────────────────────────

    def test_dict_pacto_antinupcial_contem_estados(self):
        d = get_imovel_prices_dict('pacto_antinupcial')
        for uf in ('BA', 'RJ', 'PI', 'AC', 'RN'):
            self.assertIn(uf, d)

    def test_dict_pacto_antinupcial_ba_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('pacto_antinupcial')['BA'], '699.90')

    def test_dict_pacto_antinupcial_pi_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('pacto_antinupcial')['PI'], '192.08')

    # ── API /api/preco-imovel/ ────────────────────────────────────────────────

    def test_api_pacto_antinupcial_ba(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'pacto_antinupcial', 'estado': 'BA'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '699.90')

    def test_api_pacto_antinupcial_rj(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'pacto_antinupcial', 'estado': 'RJ'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '259.90')

    def test_api_pacto_antinupcial_pi(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'pacto_antinupcial', 'estado': 'PI'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '192.08')

    def test_api_estado_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'pacto_antinupcial', 'estado': 'XX'})
        self.assertEqual(r.status_code, 404)

    def test_api_tipo_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'tipo_qualquer', 'estado': 'BA'})
        self.assertEqual(r.status_code, 404)


class CondominioPrecoTest(TestCase):
    """Testes de preço para Condomínio (chave: condominio)."""

    @classmethod
    def setUpTestData(cls):
        cls.state_ba = State.objects.create(code='BA', name='Bahia')
        cls.state_sp = State.objects.create(code='SP', name='São Paulo')
        cls.state_rj = State.objects.create(code='RJ', name='Rio de Janeiro')
        cls.state_ac = State.objects.create(code='AC', name='Acre')
        cls.state_pi = State.objects.create(code='PI', name='Piauí')
        PrecoImovelEstado.objects.create(
            tipo_certidao='condominio', state=cls.state_ba, price=Decimal('699.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='condominio', state=cls.state_sp, price=Decimal('209.95')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='condominio', state=cls.state_rj, price=Decimal('285.89')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='condominio', state=cls.state_ac, price=Decimal('160.65')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='condominio', state=cls.state_pi, price=Decimal('192.08')
        )

    # ── obter_preco_imovel ────────────────────────────────────────────────────

    def test_condominio_ba(self):
        self.assertEqual(obter_preco_imovel('condominio', 'BA'), Decimal('699.90'))

    def test_condominio_sp(self):
        self.assertEqual(obter_preco_imovel('condominio', 'SP'), Decimal('209.95'))

    def test_condominio_rj(self):
        self.assertEqual(obter_preco_imovel('condominio', 'RJ'), Decimal('285.89'))

    def test_condominio_ac_menor_preco(self):
        """AC tem o menor preço de Condomínio: R$ 160,65."""
        self.assertEqual(obter_preco_imovel('condominio', 'AC'), Decimal('160.65'))

    def test_condominio_pi_fracionado(self):
        """PI tem preço fracionado: R$ 192,08."""
        self.assertEqual(obter_preco_imovel('condominio', 'PI'), Decimal('192.08'))

    def test_condominio_estado_invalido_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('condominio', 'ZZ'))

    def test_condominio_tipo_inexistente_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('tipo_invalido', 'BA'))

    def test_condominio_estado_sem_preco_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('condominio', 'MG'))

    # ── get_imovel_prices_dict ────────────────────────────────────────────────

    def test_dict_condominio_contem_estados(self):
        d = get_imovel_prices_dict('condominio')
        for uf in ('BA', 'SP', 'RJ', 'AC', 'PI'):
            self.assertIn(uf, d)

    def test_dict_condominio_ba_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('condominio')['BA'], '699.90')

    def test_dict_condominio_sp_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('condominio')['SP'], '209.95')

    # ── API /api/preco-imovel/ ────────────────────────────────────────────────

    def test_api_condominio_ba(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'condominio', 'estado': 'BA'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '699.90')

    def test_api_condominio_sp(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'condominio', 'estado': 'SP'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '209.95')

    def test_api_condominio_rj(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'condominio', 'estado': 'RJ'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '285.89')

    def test_api_estado_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'condominio', 'estado': 'XX'})
        self.assertEqual(r.status_code, 404)

    def test_api_tipo_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'tipo_qualquer', 'estado': 'BA'})
        self.assertEqual(r.status_code, 404)


class Livro3GarantiasPrecoTest(TestCase):
    """Testes de preço para Livro 3 – Garantias (chave: livro3_garantias)."""

    @classmethod
    def setUpTestData(cls):
        cls.state_ba = State.objects.create(code='BA', name='Bahia')
        cls.state_sc = State.objects.create(code='SC', name='Santa Catarina')
        cls.state_rj = State.objects.create(code='RJ', name='Rio de Janeiro')
        cls.state_se = State.objects.create(code='SE', name='Sergipe')
        cls.state_pi = State.objects.create(code='PI', name='Piauí')
        PrecoImovelEstado.objects.create(
            tipo_certidao='livro3_garantias', state=cls.state_ba, price=Decimal('699.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='livro3_garantias', state=cls.state_sc, price=Decimal('159.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='livro3_garantias', state=cls.state_rj, price=Decimal('285.89')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='livro3_garantias', state=cls.state_se, price=Decimal('149.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='livro3_garantias', state=cls.state_pi, price=Decimal('192.08')
        )

    # ── obter_preco_imovel ────────────────────────────────────────────────────

    def test_livro3_garantias_ba(self):
        self.assertEqual(obter_preco_imovel('livro3_garantias', 'BA'), Decimal('699.90'))

    def test_livro3_garantias_sc(self):
        self.assertEqual(obter_preco_imovel('livro3_garantias', 'SC'), Decimal('159.90'))

    def test_livro3_garantias_rj(self):
        self.assertEqual(obter_preco_imovel('livro3_garantias', 'RJ'), Decimal('285.89'))

    def test_livro3_garantias_se_menor_preco(self):
        """SE tem o menor preço de Livro 3 – Garantias: R$ 149,90."""
        self.assertEqual(obter_preco_imovel('livro3_garantias', 'SE'), Decimal('149.90'))

    def test_livro3_garantias_pi_fracionado(self):
        """PI tem preço fracionado: R$ 192,08."""
        self.assertEqual(obter_preco_imovel('livro3_garantias', 'PI'), Decimal('192.08'))

    def test_livro3_garantias_estado_invalido_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('livro3_garantias', 'ZZ'))

    def test_livro3_garantias_tipo_inexistente_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('tipo_invalido', 'BA'))

    def test_livro3_garantias_estado_sem_preco_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('livro3_garantias', 'SP'))

    # ── get_imovel_prices_dict ────────────────────────────────────────────────

    def test_dict_livro3_garantias_contem_estados(self):
        d = get_imovel_prices_dict('livro3_garantias')
        for uf in ('BA', 'SC', 'RJ', 'SE', 'PI'):
            self.assertIn(uf, d)

    def test_dict_livro3_garantias_ba_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('livro3_garantias')['BA'], '699.90')

    def test_dict_livro3_garantias_sc_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('livro3_garantias')['SC'], '159.90')

    # ── API /api/preco-imovel/ ────────────────────────────────────────────────

    def test_api_livro3_garantias_ba(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'livro3_garantias', 'estado': 'BA'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '699.90')

    def test_api_livro3_garantias_sc(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'livro3_garantias', 'estado': 'SC'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '159.90')

    def test_api_livro3_garantias_rj(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'livro3_garantias', 'estado': 'RJ'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '285.89')

    def test_api_estado_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'livro3_garantias', 'estado': 'XX'})
        self.assertEqual(r.status_code, 404)

    def test_api_tipo_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'tipo_qualquer', 'estado': 'BA'})
        self.assertEqual(r.status_code, 404)


class Livro3AuxiliarPrecoTest(TestCase):
    """Testes de preço para Livro 3 – Auxiliar (chave: livro3_auxiliar)."""

    @classmethod
    def setUpTestData(cls):
        cls.state_ba = State.objects.create(code='BA', name='Bahia')
        cls.state_rs = State.objects.create(code='RS', name='Rio Grande do Sul')
        cls.state_rj = State.objects.create(code='RJ', name='Rio de Janeiro')
        cls.state_se = State.objects.create(code='SE', name='Sergipe')
        cls.state_pi = State.objects.create(code='PI', name='Piauí')
        PrecoImovelEstado.objects.create(
            tipo_certidao='livro3_auxiliar', state=cls.state_ba, price=Decimal('699.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='livro3_auxiliar', state=cls.state_rs, price=Decimal('199.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='livro3_auxiliar', state=cls.state_rj, price=Decimal('285.89')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='livro3_auxiliar', state=cls.state_se, price=Decimal('149.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='livro3_auxiliar', state=cls.state_pi, price=Decimal('192.08')
        )

    # ── obter_preco_imovel ────────────────────────────────────────────────────

    def test_livro3_auxiliar_ba(self):
        self.assertEqual(obter_preco_imovel('livro3_auxiliar', 'BA'), Decimal('699.90'))

    def test_livro3_auxiliar_rs(self):
        self.assertEqual(obter_preco_imovel('livro3_auxiliar', 'RS'), Decimal('199.90'))

    def test_livro3_auxiliar_rj(self):
        self.assertEqual(obter_preco_imovel('livro3_auxiliar', 'RJ'), Decimal('285.89'))

    def test_livro3_auxiliar_se_menor_preco(self):
        """SE tem o menor preço de Livro 3 – Auxiliar: R$ 149,90."""
        self.assertEqual(obter_preco_imovel('livro3_auxiliar', 'SE'), Decimal('149.90'))

    def test_livro3_auxiliar_pi_fracionado(self):
        """PI tem preço fracionado: R$ 192,08."""
        self.assertEqual(obter_preco_imovel('livro3_auxiliar', 'PI'), Decimal('192.08'))

    def test_livro3_auxiliar_estado_invalido_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('livro3_auxiliar', 'ZZ'))

    def test_livro3_auxiliar_tipo_inexistente_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('tipo_invalido', 'BA'))

    def test_livro3_auxiliar_estado_sem_preco_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('livro3_auxiliar', 'SP'))

    # ── get_imovel_prices_dict ────────────────────────────────────────────────

    def test_dict_livro3_auxiliar_contem_estados(self):
        d = get_imovel_prices_dict('livro3_auxiliar')
        for uf in ('BA', 'RS', 'RJ', 'SE', 'PI'):
            self.assertIn(uf, d)

    def test_dict_livro3_auxiliar_ba_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('livro3_auxiliar')['BA'], '699.90')

    def test_dict_livro3_auxiliar_rs_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('livro3_auxiliar')['RS'], '199.90')

    # ── API /api/preco-imovel/ ────────────────────────────────────────────────

    def test_api_livro3_auxiliar_ba(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'livro3_auxiliar', 'estado': 'BA'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '699.90')

    def test_api_livro3_auxiliar_rs(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'livro3_auxiliar', 'estado': 'RS'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '199.90')

    def test_api_livro3_auxiliar_rj(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'livro3_auxiliar', 'estado': 'RJ'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '285.89')

    def test_api_estado_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'livro3_auxiliar', 'estado': 'XX'})
        self.assertEqual(r.status_code, 404)

    def test_api_tipo_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'tipo_qualquer', 'estado': 'BA'})
        self.assertEqual(r.status_code, 404)


class QuesitosPrecoTest(TestCase):
    """Testes de preço para Quesitos (chave: quesitos). Último tipo — sistema completo."""

    @classmethod
    def setUpTestData(cls):
        cls.state_ba = State.objects.create(code='BA', name='Bahia')
        cls.state_rs = State.objects.create(code='RS', name='Rio Grande do Sul')
        cls.state_sp = State.objects.create(code='SP', name='São Paulo')
        cls.state_ac = State.objects.create(code='AC', name='Acre')
        cls.state_rr = State.objects.create(code='RR', name='Roraima')
        PrecoImovelEstado.objects.create(
            tipo_certidao='quesitos', state=cls.state_ba, price=Decimal('699.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='quesitos', state=cls.state_rs, price=Decimal('699.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='quesitos', state=cls.state_sp, price=Decimal('217.90')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='quesitos', state=cls.state_ac, price=Decimal('160.65')
        )
        PrecoImovelEstado.objects.create(
            tipo_certidao='quesitos', state=cls.state_rr, price=Decimal('199.90')
        )

    # ── obter_preco_imovel ────────────────────────────────────────────────────

    def test_quesitos_ba(self):
        self.assertEqual(obter_preco_imovel('quesitos', 'BA'), Decimal('699.90'))

    def test_quesitos_rs(self):
        self.assertEqual(obter_preco_imovel('quesitos', 'RS'), Decimal('699.90'))

    def test_quesitos_sp(self):
        self.assertEqual(obter_preco_imovel('quesitos', 'SP'), Decimal('217.90'))

    def test_quesitos_ac_menor_preco(self):
        """AC tem o menor preço de Quesitos: R$ 160,65."""
        self.assertEqual(obter_preco_imovel('quesitos', 'AC'), Decimal('160.65'))

    def test_quesitos_rr(self):
        self.assertEqual(obter_preco_imovel('quesitos', 'RR'), Decimal('199.90'))

    def test_quesitos_estado_invalido_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('quesitos', 'ZZ'))

    def test_quesitos_tipo_inexistente_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('tipo_invalido', 'BA'))

    def test_quesitos_estado_sem_preco_retorna_none(self):
        self.assertIsNone(obter_preco_imovel('quesitos', 'MG'))

    # ── get_imovel_prices_dict ────────────────────────────────────────────────

    def test_dict_quesitos_contem_estados(self):
        d = get_imovel_prices_dict('quesitos')
        for uf in ('BA', 'RS', 'SP', 'AC', 'RR'):
            self.assertIn(uf, d)

    def test_dict_quesitos_ba_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('quesitos')['BA'], '699.90')

    def test_dict_quesitos_sp_valor_correto(self):
        self.assertEqual(get_imovel_prices_dict('quesitos')['SP'], '217.90')

    # ── API /api/preco-imovel/ ────────────────────────────────────────────────

    def test_api_quesitos_ba(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'quesitos', 'estado': 'BA'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '699.90')

    def test_api_quesitos_rs(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'quesitos', 'estado': 'RS'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '699.90')

    def test_api_quesitos_sp(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'quesitos', 'estado': 'SP'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['display_price'], '217.90')

    def test_api_estado_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'quesitos', 'estado': 'XX'})
        self.assertEqual(r.status_code, 404)

    def test_api_tipo_inexistente_retorna_404(self):
        r = self.client.get('/api/preco-imovel/', {'tipo': 'tipo_qualquer', 'estado': 'BA'})
        self.assertEqual(r.status_code, 404)
