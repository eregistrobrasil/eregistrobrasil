from django import forms
from products.models import Product, Category, ESTADOS_BR


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
