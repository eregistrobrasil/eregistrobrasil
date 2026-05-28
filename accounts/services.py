import secrets
import string
import logging

from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

_SPECIAL = '!@#$%&*'


def gerar_senha_segura(length: int = 14) -> str:
    """Gera uma senha aleatória segura que satisfaz os requisitos mínimos de complexidade."""
    alphabet = string.ascii_letters + string.digits + _SPECIAL
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in _SPECIAL for c in password)
        if has_upper and has_lower and has_digit and has_special:
            return password


def criar_ou_obter_usuario(
    email: str,
    name: str,
    cpf: str = '',
    phone: str = '',
) -> tuple:
    """
    Obtém o usuário existente pelo e-mail ou cria um novo automaticamente.

    Retorna uma tupla (user, created, plain_password):
      - user: instância do User
      - created: True se o usuário foi criado agora
      - plain_password: senha em texto plano (somente quando created=True, senão None)
    """
    try:
        user = User.objects.get(email=email)
        logger.info('Pedido associado ao usuário existente email=%s id=%s', email, user.pk)
        return user, False, None
    except User.DoesNotExist:
        pass

    plain_password = gerar_senha_segura()
    name_parts = name.strip().split(None, 1)
    first_name = name_parts[0] if name_parts else ''
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    user = User.objects.create_user(
        username=email,
        email=email,
        password=plain_password,
        first_name=first_name,
        last_name=last_name,
    )

    # O signal post_save cria o profile automaticamente; apenas atualizamos
    profile = user.profile
    if cpf:
        profile.cpf = cpf
    if phone:
        profile.phone = phone
    profile.senha_gerada_automaticamente = True
    profile.tipo = 'cliente'
    profile.save()

    logger.info(
        'Conta criada automaticamente para email=%s user_id=%s',
        email,
        user.pk,
    )

    return user, True, plain_password
