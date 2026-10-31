from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .tasks import send_telegram_notification
from .models import Order


@receiver(post_save, sender=Order)
def notify_admin(sender, instance, created, **kwargs):
    if created:  # Check if a new record is created
        # Send the task only after the transaction is committed, so the worker sees the order
        transaction.on_commit(lambda: send_telegram_notification.delay(
            order_id=instance.id,
            product_name=instance.product.name,
            quantity=instance.quantity,
            customer_username=str(instance.customer),
            phone_number=instance.phone_number
        ))
