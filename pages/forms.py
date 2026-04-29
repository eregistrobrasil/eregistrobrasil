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
