import hmac
import json
import logging

from django.conf import settings
from django.db.models import F
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.orders.models import WhatsAppWebhookEvent

from .services import EvolutionAPIClient, EvolutionAPIError
from .webhooks import parse_evolution_webhook, process_webhook_event

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def webhook(request):
    expected = settings.EVOLUTION_WEBHOOK_SECRET
    supplied = request.headers.get("X-Webhook-Secret", "")
    if not expected or not hmac.compare_digest(supplied, expected):
        logger.warning("Invalid webhook secret")
        return JsonResponse({"detail": "Unauthorized"}, status=401)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)
    logger.info("Webhook received", extra={"event": payload.get("event")})
    result = process_webhook_event(parse_evolution_webhook(payload))
    if result.order and result.outcome in {"confirmed", "cancelled", "edit_requested", "edit_received", "already_processed"}:
        client = EvolutionAPIClient()
        try:
            if result.outcome == "confirmed":
                client.send_order_confirmed_message(result.order)
            elif result.outcome == "cancelled":
                client.send_order_cancelled_message(result.order)
            elif result.outcome == "edit_requested":
                client.send_order_edit_prompt(result.order)
            elif result.outcome == "edit_received":
                client.send_order_edit_received_message(result.order)
            else:
                client.send_already_processed_message(result.order)
            if result.webhook_event:
                WhatsAppWebhookEvent.objects.filter(pk=result.webhook_event.pk).update(
                    acknowledged_at=timezone.now(),
                    acknowledgement_attempts=F("acknowledgement_attempts") + 1,
                )
        except (EvolutionAPIError, ValueError):
            logger.exception("Evolution API error while sending webhook acknowledgement", extra={"order_number": result.order.order_number})
            if result.webhook_event:
                WhatsAppWebhookEvent.objects.filter(pk=result.webhook_event.pk).update(
                    acknowledgement_attempts=F("acknowledgement_attempts") + 1,
                )
            # Ask Evolution to retry this callback. The stored event makes the
            # order transition idempotent while allowing the reply to be sent.
            return JsonResponse({"status": result.outcome, "acknowledgement": "retry"}, status=503)
    return JsonResponse({"status": result.outcome})
