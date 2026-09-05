import hmac
import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

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
    if result.order and result.outcome in {"confirmed", "cancelled", "already_processed"}:
        client = EvolutionAPIClient()
        try:
            if result.outcome == "confirmed":
                client.send_order_confirmed_message(result.order)
            elif result.outcome == "cancelled":
                client.send_order_cancelled_message(result.order)
            else:
                client.send_already_processed_message(result.order)
        except (EvolutionAPIError, ValueError):
            logger.exception("Evolution API error while sending webhook acknowledgement", extra={"order_number": result.order.order_number})
    return JsonResponse({"status": result.outcome})
