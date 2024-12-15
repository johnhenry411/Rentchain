from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Wallet
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        # Create a wallet for the newly created user
        Wallet.objects.get_or_create(user=instance, defaults={"balance": 0.00})