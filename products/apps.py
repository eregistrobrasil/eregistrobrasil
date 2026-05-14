import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


def _auto_seed_services(sender, **kwargs):
    """
    Signal post_migrate: garante que todos os serviços do sistema existam após
    qualquer execução de `manage.py migrate`.

    - Idempotente: seed_all_services usa get_or_create por slug.
    - Seguro: captura OperationalError/ProgrammingError durante a
      primeira inicialização (quando as tabelas ainda não existem).
    """
    from django.db import OperationalError, ProgrammingError

    try:
        from django.core.management import call_command

        call_command("seed_states", verbosity=0)
        call_command("seed_all_services", verbosity=0)
    except (OperationalError, ProgrammingError):
        # Tabelas ainda não existem — ocorre somente na primeira migração
        pass
    except Exception:
        logger.exception(
            "Auto-seed falhou durante post_migrate. "
            "Execute manualmente: python manage.py seed_all_services"
        )


class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products"
    verbose_name = "Produtos e Certidões"

    def ready(self):
        import products.signals  # noqa

        from django.db.models.signals import post_migrate

        post_migrate.connect(_auto_seed_services, sender=self)
