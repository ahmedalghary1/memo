import hmac
import json
import logging

from django.conf import settings
from django.db.models import F
from django.http import JsonResponse
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from apps.orders.models import WhatsAppWebhookEvent

from .services import EvolutionAPIClient, EvolutionAPIError
from .webhooks import parse_evolution_webhook, process_webhook_event
from .meta_webhooks import process_meta_payload, valid_meta_signature

logger = logging.getLogger(__name__)


@csrf_exempt
def webhook(request):
    if request.method == "GET":
        mode = request.GET.get("hub.mode", "")
        supplied = request.GET.get("hub.verify_token", "")
        challenge = request.GET.get("hub.challenge", "")
        expected = settings.WHATSAPP_VERIFY_TOKEN
        if mode == "subscribe" and expected and challenge and hmac.compare_digest(supplied, expected):
            return HttpResponse(challenge, content_type="text/plain", status=200)
        return HttpResponse("Forbidden", status=403)
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    # Meta signs the exact raw request body with the app secret. Evolution keeps
    # its existing private-network secret authentication below.
    signature = request.headers.get("X-Hub-Signature-256", "")
    if signature:
        if not valid_meta_signature(request.body, signature):
            logger.warning("Rejected Meta WhatsApp webhook: invalid signature")
            return JsonResponse({"detail": "Unauthorized"}, status=401)
        try:
            payload = json.loads(request.body)
            if not isinstance(payload, dict):
                raise ValueError
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            return JsonResponse({"detail": "Invalid JSON payload"}, status=400)
        try:
            outcomes = process_meta_payload(payload)
            logger.info("Meta WhatsApp webhook accepted. outcomes=%s", ",".join(outcomes) or "empty")
        except Exception:
            # Acknowledge valid callbacks quickly; full payloads and credentials
            # are intentionally never written to logs.
            logger.exception("Meta WhatsApp webhook processing failed")
        return JsonResponse({"status": "ok"}, status=200)

    expected = settings.EVOLUTION_WEBHOOK_SECRET
    supplied = request.headers.get("X-Webhook-Secret", "")
    query_token = request.GET.get("token", "")
    if not expected or not (
        hmac.compare_digest(supplied, expected)
        or hmac.compare_digest(query_token, expected)
    ):
        logger.warning("Invalid webhook secret")
        return JsonResponse({"detail": "Unauthorized"}, status=401)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)
    logger.info("Webhook received", extra={"event": payload.get("event")})
    event = parse_evolution_webhook(payload)
    result = process_webhook_event(event)
    logger.info(
        "Webhook processed: %s (sender_phone=%s, chat_type=%s)",
        result.outcome,
        "available" if event.sender_phone else "missing",
        event.chat_jid.rsplit("@", 1)[-1] if "@" in event.chat_jid else "missing",
    )
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


def health(request):
    return JsonResponse({"status": "ok", "service": "whatsapp"})
