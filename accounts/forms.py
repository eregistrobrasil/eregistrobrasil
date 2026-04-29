from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        label='Nome', max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Seu nome', 'class': 'form-input'})
    )
    last_name = forms.CharField(
        label='Sobrenome', max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Seu sobrenome', 'class': 'form-input'})
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'placeholder': 'seu@email.com', 'class': 'form-input'})
    )
    cpf = forms.CharField(
        label='CPF', max_length=14,
        widget=forms.TextInput(attrs={'placeholder': '000.000.000-00', 'class': 'form-input'})
    )
    phone = forms.CharField(
        label='Telefone', max_length=20, required=False,
        widget=forms.TextInput(attrs={'placeholder': '(11) 90000-0000', 'class': 'form-input'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'cpf', 'phone', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            user.profile.cpf = self.cleaned_data.get('cpf', '')
            user.profile.phone = self.cleaned_data.get('phone', '')
            user.profile.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'placeholder': 'seu@email.com', 'class': 'form-input', 'autofocus': True})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-input'})
    )


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(label='Nome', max_length=50)
    last_name = forms.CharField(label='Sobrenome', max_length=50)
    email = forms.EmailField(label='E-mail')

    class Meta:
        model = UserProfile
        fields = ('cpf', 'phone', 'birth_date')
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
