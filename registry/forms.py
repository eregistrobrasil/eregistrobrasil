from django import forms
from .models import Registry

_INPUT = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors'
_SELECT = _INPUT

TIPO_SERVICO_CHOICES = [
    ('civil', 'Civil'),
    ('notas', 'Notas'),
    ('imoveis', 'Imóveis'),
    ('protesto', 'Protesto'),
]


class CartorioForm(forms.ModelForm):
    tipos_servico = forms.MultipleChoiceField(
        label='Tipos de Serviço',
        choices=TIPO_SERVICO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        error_messages={'required': 'Selecione ao menos um tipo de serviço.'},
    )

    class Meta:
        model = Registry
        fields = [
            'nome', 'estado', 'cidade', 'tipos_servico',
            'cnpj', 'endereco', 'email', 'telefone', 'ativo',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Ex: 1º Cartório de Registro Civil',
            }),
            'estado': forms.Select(attrs={'class': _SELECT, 'id': 'id_estado'}),
            'cidade': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Nome da cidade',
                'id': 'id_cidade',
            }),
            'cnpj': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': '00.000.000/0001-00',
                'maxlength': '18',
            }),
            'endereco': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': 'Rua, número, bairro',
            }),
            'email': forms.EmailInput(attrs={
                'class': _INPUT,
                'placeholder': 'contato@cartorio.com.br',
            }),
            'telefone': forms.TextInput(attrs={
                'class': _INPUT,
                'placeholder': '(00) 0000-0000',
                'maxlength': '20',
            }),
            'ativo': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-primary rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from products.models import ESTADOS_BR
        estado_choices = [('', '— Selecione o estado —')] + list(ESTADOS_BR)
        self.fields['estado'].widget = forms.Select(
            attrs={'class': _SELECT, 'id': 'id_estado'},
            choices=estado_choices,
        )
        self.fields['estado'].choices = estado_choices
        # Pré-carrega valores existentes do JSONField
        if self.instance and self.instance.pk:
            self.fields['tipos_servico'].initial = self.instance.tipo_servico or []

    def clean_tipos_servico(self):
        return self.cleaned_data.get('tipos_servico', [])

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Salva a lista de tipos no JSONField
        instance.tipo_servico = self.cleaned_data.get('tipos_servico', [])
        if commit:
            instance.save()
        return instance
