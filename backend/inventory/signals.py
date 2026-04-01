from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Item
from .email_service import send_low_stock_alert
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Item)
def check_low_stock(sender, instance, created, **kwargs):
    """
    Check if item stock is low after save and send email alert
    """
    if not created and instance.count < settings.LOW_STOCK_THRESHOLD:
        logger.info(f"Low stock detected for {instance.name}: {instance.count} units")

        # Send email to configured recipient
        if settings.LOW_STOCK_ALERT_EMAIL:
            send_low_stock_alert(
                item_name=instance.name,
                current_stock=instance.count,
                user_email=settings.LOW_STOCK_ALERT_EMAIL
            )
        else:
            logger.warning("LOW_STOCK_ALERT_EMAIL not configured - skipping email")
