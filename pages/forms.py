import re
from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        label='Nome', max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Seu nome', 'class': 'form-input'})
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'placeholder': 'seu@email.com', 'class': 'form-input'})
    )
    subject = forms.CharField(
        label='Assunto', max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Como podemos ajudar?', 'class': 'form-input'})
    )
    message = forms.CharField(
        label='Mensagem',
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Sua mensagem...', 'class': 'form-input'})
    )


_INPUT_CLASS = (
    'field-input w-full border border-gray-300 rounded-lg px-4 py-2.5 '
    'text-sm placeholder-gray-400 transition-all duration-200'
)


class CertidaoCartorioForm(forms.Form):
    estado = forms.CharField(
        label='Estado',
        max_length=2,
        error_messages={'required': 'Selecione um estado.'},
    )
    cidade = forms.CharField(
        label='Cidade',
        max_length=100,
        error_messages={'required': 'Selecione uma cidade.'},
    )
    cartorio_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(),
    )
    cartorio = forms.CharField(
        label='Nome do Cartório',
        max_length=200,
        required=False,
        widget=forms.HiddenInput(),
    )

    def clean(self):
        cleaned = super().clean()
        cartorio_id = cleaned.get('cartorio_id')
        if cartorio_id:
            from registry.models import Registry
            try:
                cartorio_obj = Registry.objects.get(pk=cartorio_id, ativo=True)
                cleaned['cartorio'] = cartorio_obj.nome
                cleaned['cartorio_id'] = cartorio_obj.pk
            except Registry.DoesNotExist:
                cleaned['cartorio_id'] = None
                cleaned['cartorio'] = cleaned.get('cartorio') or 'Cartório não informado'
        else:
            if not cleaned.get('cartorio'):
                cleaned['cartorio'] = 'Cartório não informado'
        return cleaned


class CertidaoRegistroForm(forms.Form):
    nome_completo = forms.CharField(
        label='Nome Completo',
        max_length=200,
        error_messages={'required': 'Informe o nome completo.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Nome completo da pessoa',
            'autocomplete': 'name',
        }),
    )
    nome_mae = forms.CharField(
        label='Nome Completo da Mãe',
        max_length=200,
        error_messages={'required': 'Informe o nome completo da mãe.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Nome completo da mãe',
        }),
    )
    nome_pai = forms.CharField(
        label='Nome Completo do Pai',
        max_length=200,
        error_messages={'required': 'Informe o nome completo do pai.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Nome completo do pai',
        }),
    )
    data_nascimento = forms.DateField(
        label='Data de Nascimento',
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        error_messages={
            'required': 'Informe a data de nascimento.',
            'invalid': 'Data inválida. Use o formato DD/MM/AAAA.',
        },
        widget=forms.TextInput(attrs={
            'id': 'id_data_nascimento',
            'class': _INPUT_CLASS,
            'placeholder': 'DD/MM/AAAA',
            'autocomplete': 'bday',
            'inputmode': 'numeric',
            'maxlength': '10',
        }),
    )
    numero_livro = forms.CharField(
        label='Número do Livro',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: A-10 (opcional)',
        }),
    )
    numero_folha = forms.CharField(
        label='Número da Folha',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: 123 (opcional)',
        }),
    )
    numero_termo = forms.CharField(
        label='Número do Termo',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: 456 (opcional)',
        }),
    )


# ─────────────────────────────────────────────
#  Helpers reutilizáveis
# ─────────────────────────────────────────────

def _date_field(label, required=True, msg_label=None):
    lbl = msg_label or label.lower()
    return forms.DateField(
        label=label,
        required=required,
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        error_messages={
            'required': f'Informe {lbl}.',
            'invalid': 'Data inválida. Use o formato DD/MM/AAAA.',
        },
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'DD/MM/AAAA',
            'inputmode': 'numeric',
            'maxlength': '10',
        }),
    )


def _char_field(label, placeholder='', required=True, max_length=200, msg_label=None):
    lbl = msg_label or label.lower()
    kw = {
        'label': label,
        'max_length': max_length,
        'required': required,
        'widget': forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': placeholder or label,
        }),
    }
    if required:
        kw['error_messages'] = {'required': f'Informe {lbl}.'}
    return forms.CharField(**kw)


def _livro_folha_termo():
    return {
        'numero_livro': forms.CharField(
            label='Número do Livro', max_length=50, required=False,
            widget=forms.TextInput(attrs={'class': _INPUT_CLASS, 'placeholder': 'Ex: A-10 (opcional)'}),
        ),
        'numero_folha': forms.CharField(
            label='Número da Folha', max_length=50, required=False,
            widget=forms.TextInput(attrs={'class': _INPUT_CLASS, 'placeholder': 'Ex: 123 (opcional)'}),
        ),
        'numero_termo': forms.CharField(
            label='Número do Termo', max_length=50, required=False,
            widget=forms.TextInput(attrs={'class': _INPUT_CLASS, 'placeholder': 'Ex: 456 (opcional)'}),
        ),
    }


def _cpf_field():
    return forms.CharField(
        label='CPF',
        max_length=14,
        error_messages={'required': 'Informe o CPF.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': '000.000.000-00',
            'inputmode': 'numeric',
            'maxlength': '14',
            'data-mask': 'cpf',
        }),
    )


# ─────────────────────────────────────────────
#  Certidão de Óbito
# ─────────────────────────────────────────────

class CertidaoObitoForm(forms.Form):
    nome_completo = _char_field('Nome Completo', 'Nome completo da pessoa')
    nome_mae = _char_field('Nome Completo da Mãe', 'Nome completo da mãe', msg_label='o nome completo da mãe')
    nome_pai = _char_field('Nome Completo do Pai', 'Nome completo do pai', msg_label='o nome completo do pai')
    data_obito = _date_field('Data do Óbito', msg_label='a data do óbito')
    numero_livro = forms.CharField(
        label='Número do Livro', max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': _INPUT_CLASS, 'placeholder': 'Ex: A-10 (opcional)'}),
    )
    numero_folha = forms.CharField(
        label='Número da Folha', max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': _INPUT_CLASS, 'placeholder': 'Ex: 123 (opcional)'}),
    )
    numero_termo = forms.CharField(
        label='Número do Termo', max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': _INPUT_CLASS, 'placeholder': 'Ex: 456 (opcional)'}),
    )


# ─────────────────────────────────────────────
#  Certidão de Casamento
# ─────────────────────────────────────────────

class CertidaoCasamentoForm(forms.Form):
    conjuge_1 = _char_field('Nome do Cônjuge 1', 'Nome completo do cônjuge 1', msg_label='o nome do cônjuge 1')
    conjuge_2 = _char_field('Nome do Cônjuge 2', 'Nome completo do cônjuge 2', msg_label='o nome do cônjuge 2')
    data_casamento = _date_field('Data do Casamento', msg_label='a data do casamento')
    numero_livro = forms.CharField(
        label='Número do Livro', max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': _INPUT_CLASS, 'placeholder': 'Ex: A-10 (opcional)'}),
    )
    numero_folha = forms.CharField(
        label='Número da Folha', max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': _INPUT_CLASS, 'placeholder': 'Ex: 123 (opcional)'}),
    )
    numero_termo = forms.CharField(
        label='Número do Termo', max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': _INPUT_CLASS, 'placeholder': 'Ex: 456 (opcional)'}),
    )


# ─────────────────────────────────────────────
#  Certidão de Interdição
# ─────────────────────────────────────────────

class CertidaoInterdicaoForm(forms.Form):
    cpf = _cpf_field()
    nome_completo = _char_field('Nome Completo', 'Nome completo da pessoa')
    nome_mae = _char_field('Nome da Mãe', 'Nome da mãe', msg_label='o nome da mãe')
    nome_pai = _char_field('Nome do Pai', 'Nome do pai', msg_label='o nome do pai')
    data_nascimento = _date_field('Data de Nascimento', msg_label='a data de nascimento')
    estado_nascimento = forms.CharField(
        label='Estado de Nascimento',
        max_length=2,
        error_messages={'required': 'Selecione o estado de nascimento.'},
    )
    cidade_nascimento = forms.CharField(
        label='Cidade de Nascimento',
        max_length=100,
        error_messages={'required': 'Informe a cidade de nascimento.'},
        widget=forms.TextInput(attrs={'class': _INPUT_CLASS, 'placeholder': 'Cidade de nascimento'}),
    )
    rg = _char_field('RG', 'Número do RG', msg_label='o RG')
    ano_ato = forms.CharField(
        label='Ano Aproximado do Ato',
        max_length=4,
        error_messages={'required': 'Informe o ano aproximado do ato.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: 2010',
            'inputmode': 'numeric',
            'maxlength': '4',
        }),
    )

    def clean_cpf(self):
        cpf = re.sub(r'\D', '', self.cleaned_data.get('cpf', ''))
        if len(cpf) != 11:
            raise forms.ValidationError('CPF inválido. Informe os 11 dígitos.')
        return cpf

    def clean_ano_ato(self):
        ano = self.cleaned_data.get('ano_ato', '').strip()
        if not re.match(r'^\d{4}$', ano):
            raise forms.ValidationError('Informe um ano válido com 4 dígitos.')
        return ano


# ─────────────────────────────────────────────
#  Certidão de Procuração
# ─────────────────────────────────────────────

class CertidaoProcuracaoForm(forms.Form):
    cpf = _cpf_field()
    nome_completo = _char_field('Nome Completo', 'Nome completo da pessoa')
    numero_livro = forms.CharField(
        label='Número do Livro',
        max_length=50,
        required=True,
        error_messages={'required': 'Informe o número do livro.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: A-10',
            'inputmode': 'text',
        }),
    )
    numero_pagina = forms.CharField(
        label='Número da Página',
        max_length=50,
        required=True,
        error_messages={'required': 'Informe o número da página.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: 55',
            'inputmode': 'numeric',
        }),
    )
    data_ato = _date_field('Data do Ato', required=False, msg_label='a data do ato')

    def clean_cpf(self):
        cpf = re.sub(r'\D', '', self.cleaned_data.get('cpf', ''))
        if len(cpf) != 11:
            raise forms.ValidationError('CPF inválido. Informe os 11 dígitos.')
        return cpf

    def clean_numero_livro(self):
        valor = self.cleaned_data.get('numero_livro', '').strip()
        if not valor:
            raise forms.ValidationError('Informe o número do livro.')
        return valor

    def clean_numero_pagina(self):
        valor = self.cleaned_data.get('numero_pagina', '').strip()
        if not valor:
            raise forms.ValidationError('Informe o número da página.')
        return valor


# ─────────────────────────────────────────────
#  Certidão de Imóvel — tipos e forms dinâmicos
# ─────────────────────────────────────────────

TIPOS_CERTIDAO_IMOVEL = [
    ('matricula',         'Matrícula'),
    ('inteiro_teor',      'Certidão de Inteiro Teor e Ônus da Ação'),
    ('vintenaria',        'Vintenária'),
    ('transcricao',       'Transcrição'),
    ('doc_arquivado',     'Documento Arquivado'),
    ('pacto_antinupcial', 'Pacto Antinupcial'),
    ('condominio',        'Condomínio'),
    ('livro3_garantias',  'Livro 3 – Garantias'),
    ('livro3_auxiliar',   'Livro 3 – Auxiliar'),
    ('quesitos',          'Quesitos'),
]

TIPOS_CERTIDAO_IMOVEL_DICT = dict(TIPOS_CERTIDAO_IMOVEL)


def _matricula_field():
    return forms.CharField(
        label='Número da Matrícula',
        max_length=50,
        error_messages={'required': 'Informe o número da matrícula.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: 12345',
            'inputmode': 'numeric',
        }),
    )


class CertidaoImovelMatriculaForm(forms.Form):
    numero_matricula = _matricula_field()


class CertidaoImovelInteiroTeorForm(forms.Form):
    numero_matricula = _matricula_field()


class CertidaoImovelVintenariaForm(forms.Form):
    numero_matricula = _matricula_field()


class CertidaoImovelQuesitosForm(forms.Form):
    numero_matricula = _matricula_field()


class CertidaoImovelTranscricaoForm(forms.Form):
    numero_transcricao = _char_field(
        'Número da Transcrição', 'Ex: 12345', msg_label='o número da transcrição'
    )
    data_emissao      = _date_field('Data de Emissão', required=False, msg_label='a data de emissão')
    livro             = _char_field('Livro', 'Ex: B-10', required=False, msg_label='o livro')
    # Dados do imóvel (complementares)
    imovel_cidade      = _char_field('Cidade do Imóvel',  '', required=False)
    imovel_rua         = _char_field('Rua',               '', required=False)
    imovel_numero      = _char_field('Número',            '', required=False, max_length=20)
    imovel_lote        = _char_field('Lote',              '', required=False, max_length=20)
    imovel_apartamento = _char_field('Apartamento',       '', required=False, max_length=20)
    imovel_bloco       = _char_field('Bloco',             '', required=False, max_length=20)
    imovel_andar       = _char_field('Andar',             '', required=False, max_length=20)
    imovel_edificio    = _char_field('Edifício',          '', required=False)
    imovel_bairro      = _char_field('Bairro',            '', required=False)
    imovel_vila        = _char_field('Vila',              '', required=False)


_DOC_ARQUIVADO_CHOICES = [
    ('',                'Selecione o tipo'),
    ('matricula',       'Matrícula'),
    ('registro_livro3', 'Registro Livro 3'),
    ('protocolo',       'Protocolo'),
]


class CertidaoImovelDocArquivadoForm(forms.Form):
    tipo_referencia = forms.ChoiceField(
        label='Tipo de Referência',
        choices=_DOC_ARQUIVADO_CHOICES,
        error_messages={'required': 'Selecione o tipo de referência.'},
        widget=forms.Select(attrs={'class': _INPUT_CLASS, 'id': 'id_tipo_referencia'}),
    )
    numero_referencia = _char_field(
        'Número de Referência', 'Informe o número correspondente',
        msg_label='o número de referência'
    )

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo_referencia')
        numero = cleaned.get('numero_referencia', '').strip()
        if tipo and not numero:
            self.add_error('numero_referencia', 'Informe o número correspondente ao tipo selecionado.')
        return cleaned


class CertidaoImovelCondominioForm(forms.Form):
    nome_condominio = _char_field(
        'Nome do Condomínio', 'Nome completo do condomínio', msg_label='o nome do condomínio'
    )


def _imovel_clean_cpf(form_instance):
    cpf = re.sub(r'\D', '', form_instance.cleaned_data.get('cpf', ''))
    if len(cpf) != 11:
        raise forms.ValidationError('CPF inválido. Informe os 11 dígitos.')
    return cpf


class CertidaoImovelLivro3GarantiasForm(forms.Form):
    nome_completo = _char_field('Nome Completo', 'Nome completo', msg_label='o nome completo')
    cpf = _cpf_field()

    def clean_cpf(self):
        return _imovel_clean_cpf(self)


class CertidaoImovelLivro3AuxiliarForm(forms.Form):
    nome_completo = _char_field('Nome Completo', 'Nome completo', msg_label='o nome completo')
    cpf = _cpf_field()

    def clean_cpf(self):
        return _imovel_clean_cpf(self)


class CertidaoImovelPactoAntinupcialForm(forms.Form):
    nome_completo = _char_field(
        'Nome Completo do Outorgante', 'Nome completo', msg_label='o nome completo'
    )
    cpf = _cpf_field()

    def clean_cpf(self):
        return _imovel_clean_cpf(self)


# Mapeamento tipo → form class (exportado para views)
IMOVEL_FORM_MAP = {
    'matricula':         CertidaoImovelMatriculaForm,
    'inteiro_teor':      CertidaoImovelInteiroTeorForm,
    'vintenaria':        CertidaoImovelVintenariaForm,
    'transcricao':       CertidaoImovelTranscricaoForm,
    'doc_arquivado':     CertidaoImovelDocArquivadoForm,
    'pacto_antinupcial': CertidaoImovelPactoAntinupcialForm,
    'condominio':        CertidaoImovelCondominioForm,
    'livro3_garantias':  CertidaoImovelLivro3GarantiasForm,
    'livro3_auxiliar':   CertidaoImovelLivro3AuxiliarForm,
    'quesitos':          CertidaoImovelQuesitosForm,
}


# ─────────────────────────────────────────────
#  Certidão de Penhor de Safra
# ─────────────────────────────────────────────

_TIPO_SAFRA_CHOICES = [
    ('',            'Selecione o tipo'),
    ('soja',        'Soja'),
    ('milho',       'Milho'),
    ('cana',        'Cana-de-Açúcar'),
    ('algodao',     'Algodão'),
    ('cafe',        'Café'),
    ('trigo',       'Trigo'),
    ('arroz',       'Arroz'),
    ('feijao',      'Feijão'),
    ('outros',      'Outros'),
]


class CertidaoPenhorSafraForm(forms.Form):
    nome_completo = _char_field(
        'Nome da Pessoa', 'Nome completo', msg_label='o nome completo'
    )
    cpf = _cpf_field()
    tipo_safra = forms.ChoiceField(
        label='Tipo de Safra',
        choices=_TIPO_SAFRA_CHOICES,
        error_messages={'required': 'Selecione o tipo de safra.'},
        widget=forms.Select(attrs={'class': _INPUT_CLASS}),
    )
    data_ato = _date_field('Data', msg_label='a data do ato')
    numero_registro = forms.CharField(
        label='Número de Registro',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: 12345 (opcional)',
        }),
    )
    nome_propriedade = forms.CharField(
        label='Nome da Propriedade',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: Fazenda São João (opcional)',
        }),
    )

    def clean_cpf(self):
        cpf = re.sub(r'\D', '', self.cleaned_data.get('cpf', ''))
        if len(cpf) != 11:
            raise forms.ValidationError('CPF inválido. Informe os 11 dígitos.')
        return cpf

    def clean_tipo_safra(self):
        valor = self.cleaned_data.get('tipo_safra', '').strip()
        if not valor:
            raise forms.ValidationError('Selecione o tipo de safra.')
        return valor


# ─────────────────────────────────────────────
#  Certidão de Escritura
# ─────────────────────────────────────────────

class CertidaoEscrituraForm(forms.Form):
    cpf = _cpf_field()
    nome_completo = _char_field('Nome Completo', 'Nome completo da pessoa')
    numero_livro = forms.CharField(
        label='Número do Livro',
        max_length=50,
        required=True,
        error_messages={'required': 'Informe o número do livro.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: A-10',
            'inputmode': 'text',
        }),
    )
    numero_pagina = forms.CharField(
        label='Número da Página',
        max_length=50,
        required=True,
        error_messages={'required': 'Informe o número da página.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: 55',
            'inputmode': 'numeric',
        }),
    )
    data_ato = _date_field('Data do Ato', required=False, msg_label='a data do ato')

    def clean_cpf(self):
        cpf = re.sub(r'\D', '', self.cleaned_data.get('cpf', ''))
        if len(cpf) != 11:
            raise forms.ValidationError('CPF inválido. Informe os 11 dígitos.')
        return cpf

    def clean_numero_livro(self):
        valor = self.cleaned_data.get('numero_livro', '').strip()
        if not valor:
            raise forms.ValidationError('Informe o número do livro.')
        return valor

    def clean_numero_pagina(self):
        valor = self.cleaned_data.get('numero_pagina', '').strip()
        if not valor:
            raise forms.ValidationError('Informe o número da página.')
        return valor


# ─────────────────────────────────────────────
#  Certidão de Escritura de União Estável
# ─────────────────────────────────────────────

class CertidaoUniaoEstavelForm(forms.Form):
    cpf = _cpf_field()
    nome_completo = _char_field('Nome Completo', 'Nome completo da pessoa')
    numero_livro = forms.CharField(
        label='Número do Livro',
        max_length=50,
        required=True,
        error_messages={'required': 'Informe o número do livro.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: A-10',
            'inputmode': 'text',
        }),
    )
    numero_pagina = forms.CharField(
        label='Número da Página',
        max_length=50,
        required=True,
        error_messages={'required': 'Informe o número da página.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Ex: 55',
            'inputmode': 'numeric',
        }),
    )
    data_ato = _date_field('Data do Ato', required=False, msg_label='a data do ato')

    def clean_cpf(self):
        cpf = re.sub(r'\D', '', self.cleaned_data.get('cpf', ''))
        if len(cpf) != 11:
            raise forms.ValidationError('CPF inválido. Informe os 11 dígitos.')
        return cpf

    def clean_numero_livro(self):
        valor = self.cleaned_data.get('numero_livro', '').strip()
        if not valor:
            raise forms.ValidationError('Informe o número do livro.')
        return valor

    def clean_numero_pagina(self):
        valor = self.cleaned_data.get('numero_pagina', '').strip()
        if not valor:
            raise forms.ValidationError('Informe o número da página.')
        return valor


# ─────────────────────────────────────────────
#  Pacote de Certidões — Compra e Venda de Imóvel
# ─────────────────────────────────────────────

class PacoteCertidoesCompraVendaForm(forms.Form):
    nome_completo = _char_field('Nome Completo', 'Nome completo do solicitante', msg_label='o nome completo')
    cpf = _cpf_field()
    endereco = forms.CharField(
        label='Endereço',
        max_length=300,
        error_messages={'required': 'Informe o endereço completo.'},
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Rua, número, bairro, cidade — UF',
            'autocomplete': 'street-address',
        }),
    )
    nome_mae = _char_field('Nome da Mãe', 'Nome completo da mãe', msg_label='o nome da mãe')

    def clean_cpf(self):
        cpf = re.sub(r'\D', '', self.cleaned_data.get('cpf', ''))
        if len(cpf) != 11:
            raise forms.ValidationError('CPF inválido. Informe os 11 dígitos.')
        return cpf

