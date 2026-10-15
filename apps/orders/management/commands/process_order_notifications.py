import logging
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.orders.models import OrderNotification
from apps.orders.whatsapp.services import send_order_confirmation_safely

logger = logging.getLogger(__name__)


def process_one_notification():
    with transaction.atomic():
        notification = (OrderNotification.objects.select_for_update(skip_locked=True)
                        .filter(sent_at__isnull=True, next_attempt_at__lte=timezone.now())
                        .order_by("next_attempt_at", "pk").first())
        if notification is None:
            return False
        if notification.order.status in {"cancelled", "returned"}:
            notification.sent_at = timezone.now()
            notification.last_error = "Order no longer requires confirmation"
            notification.save(update_fields=["sent_at", "last_error"])
            return True
        sent = send_order_confirmation_safely(notification.order_id)
        notification.attempts += 1
        if sent:
            notification.sent_at = timezone.now()
            notification.last_error = ""
        else:
            notification.last_error = "WhatsApp provider did not confirm delivery"
            notification.next_attempt_at = timezone.now() + timedelta(seconds=min(3600, 30 * 2 ** min(notification.attempts, 7)))
            logger.warning("Order notification retry scheduled for order_id=%s", notification.order_id)
        notification.save(update_fields=["attempts", "sent_at", "last_error", "next_attempt_at"])
        return True


class Command(BaseCommand):
    help = "Send pending order confirmations with database-backed retries."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        while True:
            try:
                processed = process_one_notification()
            except Exception:
                logger.exception("Order notification worker error")
                processed = False
            if options["once"]:
                return
            if not processed:
                time.sleep(5)
