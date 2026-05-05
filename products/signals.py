from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product


@receiver(post_save, sender=Product)
def criar_precos_por_estado(sender, instance, created, **kwargs):
    """Ao criar um novo produto, gera automaticamente ServiceStatePrice para todos os estados."""
    if created:
        # Import aqui para evitar circular import
        from products.services import criar_precos_para_todos_estados
        criar_precos_para_todos_estados(instance)
