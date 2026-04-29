from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('customer_name', 'customer_email', 'customer_cpf', 'customer_phone', 'notes')
        widgets = {
            'customer_name': forms.TextInput(attrs={'placeholder': 'Nome completo', 'class': 'form-input'}),
            'customer_email': forms.EmailInput(attrs={'placeholder': 'seu@email.com', 'class': 'form-input'}),
            'customer_cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00', 'class': 'form-input'}),
            'customer_phone': forms.TextInput(attrs={'placeholder': '(11) 90000-0000', 'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observações (opcional)', 'class': 'form-input'}),
        }
        labels = {
            'customer_name': 'Nome Completo',
            'customer_email': 'E-mail',
            'customer_cpf': 'CPF',
            'customer_phone': 'Telefone',
            'notes': 'Observações',
        }
