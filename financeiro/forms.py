from django import forms
from products.models import Product, Category, ESTADOS_BR, State, ServiceStatePrice


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'tipo', 'description', 'short_description',
                  'price', 'original_price', 'delivery_days', 'is_active', 'is_featured', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'short_description': forms.TextInput(attrs={'class': 'form-input'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'original_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'delivery_days': forms.NumberInput(attrs={'class': 'form-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class PriceUpdateForm(forms.Form):
    price = forms.DecimalField(
        label='Novo Preço',
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'})
    )
    original_price = forms.DecimalField(
        label='Preço Promocional (original)',
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'})
    )


class RelatorioFilterForm(forms.Form):
    data_inicio = forms.DateField(
        label='De',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'})
    )
    data_fim = forms.DateField(
        label='Até',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'})
    )


class ServicoFilterForm(forms.Form):
    q = forms.CharField(
        label='Buscar',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Nome do serviço...', 'class': 'form-input'})
    )
    categoria = forms.ModelChoiceField(
        label='Categoria',
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label='Todas as categorias',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    ativo = forms.ChoiceField(
        label='Status',
        choices=[('', 'Todos'), ('1', 'Ativos'), ('0', 'Inativos')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    estado = forms.ChoiceField(
        label='Estado',
        choices=[('', 'Todos os estados')] + list(ESTADOS_BR),
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'})
    )


# ─── Formulários do módulo Preços por Estado ──────────────────────────────────

class ServiceStatePriceForm(forms.ModelForm):
    """Formulário para criação e edição de ServiceStatePrice."""

    class Meta:
        model = ServiceStatePrice
        fields = ['service', 'state', 'price', 'promotional_price', 'is_active', 'observacao']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-input'}),
            'state': forms.Select(attrs={'class': 'form-input'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'placeholder': '0,00'
            }),
            'promotional_price': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'placeholder': '0,00 (opcional)'
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 2,
                'placeholder': 'Observação interna (opcional)...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = (
            Product.objects.filter(is_active=True)
            .select_related('category')
            .order_by('category__order', 'order', 'name')
        )
        self.fields['state'].queryset = State.objects.order_by('name')
        self.fields['promotional_price'].required = False
        self.fields['observacao'].required = False

    def clean(self):
        cleaned = super().clean()
        service = cleaned.get('service')
        state = cleaned.get('state')
        price = cleaned.get('price')
        promo = cleaned.get('promotional_price')

        if service and state:
            qs = ServiceStatePrice.objects.filter(service=service, state=state)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f'Já existe um preço configurado para "{service.name}" no estado {state.code}.'
                )

        if price and price <= 0:
            self.add_error('price', 'O preço deve ser maior que zero.')

        if promo and price and promo >= price:
            self.add_error(
                'promotional_price',
                'O preço promocional deve ser menor que o preço principal.'
            )

        return cleaned


class PrecoFilterForm(forms.Form):
    """Filtros avançados para a listagem de preços por estado."""
    q = forms.CharField(
        label='Buscar',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Serviço, categoria...', 'class': 'form-input'
        })
    )
    servico = forms.ModelChoiceField(
        label='Serviço',
        queryset=Product.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label='Todos os serviços',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    categoria = forms.ModelChoiceField(
        label='Categoria',
        queryset=Category.objects.filter(is_active=True).order_by('order', 'name'),
        required=False,
        empty_label='Todas as categorias',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    estado = forms.ChoiceField(
        label='Estado',
        choices=[('', 'Todos os estados')] + list(ESTADOS_BR),
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    ativo = forms.ChoiceField(
        label='Status',
        choices=[('', 'Todos'), ('1', 'Ativos'), ('0', 'Inativos')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    preco_min = forms.DecimalField(
        label='Preço mínimo',
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input', 'step': '0.01', 'placeholder': 'R$ 0,00'
        })
    )
    preco_max = forms.DecimalField(
        label='Preço máximo',
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input', 'step': '0.01', 'placeholder': 'R$ 999,99'
        })
    )


class MassUpdateForm(forms.Form):
    """Formulário para reajuste em massa de preços."""
    TIPO_CHOICES = [
        ('percentual', 'Reajuste percentual (%)'),
        ('fixo_adicionar', 'Adicionar valor fixo (R$)'),
        ('fixo_subtrair', 'Subtrair valor fixo (R$)'),
        ('definir', 'Definir valor exato (R$)'),
    ]
    tipo = forms.ChoiceField(
        label='Tipo de Reajuste',
        choices=TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    valor = forms.DecimalField(
        label='Valor',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input', 'step': '0.01', 'placeholder': 'Ex: 10 para 10% ou R$ 10,00'
        })
    )
    categoria = forms.ModelChoiceField(
        label='Categoria (opcional)',
        queryset=Category.objects.filter(is_active=True).order_by('order', 'name'),
        required=False,
        empty_label='Todas as categorias',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    estado = forms.ChoiceField(
        label='Estado (opcional)',
        choices=[('', 'Todos os estados')] + list(ESTADOS_BR),
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    apenas_ativos = forms.BooleanField(
        label='Apenas registros ativos',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-fin rounded'})
    )
    observacao = forms.CharField(
        label='Observação (para auditoria)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ex: Reajuste anual 2025...'
        })
    )


class ReplicarPrecosForm(forms.Form):
    """Formulário para replicar preços de um serviço para outros estados."""
    servico_origem = forms.ModelChoiceField(
        label='Serviço de Origem',
        queryset=Product.objects.filter(is_active=True).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    estado_origem = forms.ChoiceField(
        label='Estado de Origem',
        choices=[('', 'Selecione...')] + list(ESTADOS_BR),
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    servico_destino = forms.ModelChoiceField(
        label='Serviço de Destino',
        queryset=Product.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label='Mesmo serviço (replicar para outros estados)',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    estados_destino = forms.MultipleChoiceField(
        label='Estados de Destino',
        choices=ESTADOS_BR,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'text-sm'})
    )
    sobrescrever = forms.BooleanField(
        label='Sobrescrever preços existentes',
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-fin rounded'})
    )
