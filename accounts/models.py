from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    TIPO_CHOICES = [
        ('admin', 'Administrador'),
        ('operador', 'Operador'),
        ('financeiro', 'Financeiro'),
        ('cliente', 'Cliente'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    tipo = models.CharField('Tipo', max_length=15, choices=TIPO_CHOICES, default='cliente')
    cpf = models.CharField('CPF', max_length=14, blank=True)
    phone = models.CharField('Telefone', max_length=20, blank=True)
    birth_date = models.DateField('Data de Nascimento', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    senha_gerada_automaticamente = models.BooleanField(
        'Senha gerada automaticamente', default=False
    )
    senha_alterada_pelo_usuario = models.BooleanField(
        'Senha alterada pelo usuário', default=False
    )

    class Meta:
        verbose_name = 'Perfil do Usuário'
        verbose_name_plural = 'Perfis dos Usuários'

    def __str__(self):
        return f'Perfil de {self.user.get_full_name() or self.user.username}'

    @property
    def is_operador(self):
        return self.tipo in ('admin', 'operador')

    @property
    def is_financeiro(self):
        return self.tipo in ('admin', 'financeiro')

    @property
    def is_admin(self):
        return self.tipo == 'admin'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
