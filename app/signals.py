from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Desativado, Ativado
from .websockets import broadcast_refresh

@receiver(post_save, sender=Desativado)
def desativar_ativado(sender, instance, **kwargs):
    if instance.ativado:
        instance.ativado.ativo = False
        instance.ativado.save()


@receiver(post_delete, sender=Ativado)
def broadcast_on_delete(sender, instance, **kwargs):
    try:
        broadcast_refresh()
    except Exception as e:
        print(f"Erro ao notificar deleção: {e}")        