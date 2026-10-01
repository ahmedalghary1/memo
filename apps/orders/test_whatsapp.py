import json
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.orders.models import Order, OrderItem, WhatsAppWebhookEvent
from apps.orders.whatsapp.services import EvolutionAPIClient, EvolutionAPIError, make_order_reference, normalize_phone_number


class PhoneNormalizationTests(SimpleTestCase):
    def test_normalizes_supported_egyptian_formats(self):
        self.assertEqual(normalize_phone_number("01012345678"), "201012345678")
        self.assertEqual(normalize_phone_number("+201012345678"), "201012345678")
        self.assertEqual(normalize_phone_number("201012345678"), "201012345678")


class EvolutionAPIClientTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            status="pending_confirmation", subtotal=500, shipping_total=70, grand_total=570,
            customer_name="Customer", customer_phone="01012345678", governorate="Cairo",
            area="Nasr City", address_line="Street 1", payment_method="cash",
        )
        OrderItem.objects.create(
            order=self.order, product_name="T-Shirt", variant_sku="TEE-B-M", size_name="M",
            color_name="Black", unit_price=500, quantity=1, line_total=500,
        )

    @override_settings(EVOLUTION_USE_BUTTONS=True)
    def test_order_confirmation_uses_buttons_and_marks_it_sent(self):
        client = EvolutionAPIClient()
        with patch.object(client, "send_buttons", return_value={} ) as mocked_buttons:
            self.assertTrue(client.send_order_confirmation(self.order))
        self.order.refresh_from_db()
        self.assertIsNotNone(self.order.whatsapp_confirmation_sent_at)
        buttons = mocked_buttons.call_args.args[2]
        self.assertEqual(len(buttons), 3)
        self.assertEqual([button["displayText"] for button in buttons], [
            "✅ تأكيد الطلب", "✏️ تعديل الطلب", "❌ إلغاء الطلب",
        ])
        self.assertTrue(buttons[1]["id"].startswith("edit_order_"))

    @override_settings(EVOLUTION_USE_BUTTONS=True)
    def test_order_confirmation_falls_back_to_text(self):
        client = EvolutionAPIClient()
        with patch.object(client, "send_buttons", side_effect=EvolutionAPIError("unsupported")), patch.object(client, "send_text", return_value={}) as mocked_text:
            self.assertTrue(client.send_order_confirmation(self.order))
        self.assertIn("للتأكيد أرسل: 1", mocked_text.call_args.args[1])

    @override_settings(EVOLUTION_USE_BUTTONS=False)
    def test_order_confirmation_uses_reliable_text_mode_by_default(self):
        client = EvolutionAPIClient()
        with patch.object(client, "send_text", return_value={}) as mocked_text, patch.object(client, "send_buttons") as mocked_buttons:
            self.assertTrue(client.send_order_confirmation(self.order))
        mocked_buttons.assert_not_called()
        self.assertIn("للتأكيد أرسل: 1", mocked_text.call_args.args[1])

    def test_configure_webhook_uses_secret_header_and_messages_event(self):
        client = EvolutionAPIClient()
        with patch.object(client, "_post", return_value={}) as mocked_post:
            client.configure_webhook("https://store.example/api/whatsapp/webhook/", "secret")
        endpoint, payload = mocked_post.call_args.args
        self.assertEqual(endpoint, "webhook/set")
        self.assertEqual(payload["webhook"]["headers"], {"X-Webhook-Secret": "secret"})
        self.assertEqual(payload["webhook"]["events"], ["MESSAGES_UPSERT"])

    def test_webhook_configuration_is_verified_without_exposing_secret(self):
        client = EvolutionAPIClient()
        with patch.object(client, "_get", return_value={
            "enabled": True,
            "url": "http://web:8000/api/whatsapp/webhook/",
            "headers": {"X-Webhook-Secret": "secret"},
            "events": ["MESSAGES_UPSERT"],
        }):
            self.assertTrue(client.webhook_matches(
                "http://web:8000/api/whatsapp/webhook/", "secret",
            ))

    def test_internal_nginx_webhook_is_allowed(self):
        client = EvolutionAPIClient()
        with patch.object(client, "_post", return_value={}):
            client.configure_webhook("http://nginx/api/whatsapp/webhook/", "secret")

    def test_internal_web_service_webhook_is_allowed(self):
        client = EvolutionAPIClient()
        with patch.object(client, "_post", return_value={}):
            client.configure_webhook("http://web:8000/api/whatsapp/webhook/", "secret")

    def test_ensure_instance_creates_missing_instance(self):
        client = EvolutionAPIClient(instance="memo-store")
        with patch.object(client, "_get", return_value=[]), patch.object(client, "_post", return_value={}) as mocked_post:
            self.assertTrue(client.ensure_instance())
        mocked_post.assert_called_once_with(
            "instance/create",
            {"instanceName": "memo-store", "qrcode": True, "integration": "WHATSAPP-BAILEYS"},
            include_instance=False,
        )

    def test_ensure_instance_keeps_existing_instance(self):
        client = EvolutionAPIClient(instance="memo-store")
        with patch.object(client, "_get", return_value=[{"name": "memo-store"}]), patch.object(client, "_post") as mocked_post:
            self.assertFalse(client.ensure_instance())
        mocked_post.assert_not_called()


@override_settings(EVOLUTION_WEBHOOK_SECRET="test-webhook-secret")
class WhatsAppWebhookTests(TestCase):
    def setUp(self):
        self.url = reverse("whatsapp:webhook")
        self.order = self.create_order()

    def create_order(self, **overrides):
        data = {
            "subtotal": 500,
            "shipping_total": 70,
            "grand_total": 570,
            "customer_name": "Customer",
            "customer_phone": "01012345678",
            "customer_email": "customer@example.com",
            "governorate": "Cairo",
            "area": "Nasr City",
            "address_line": "Street 1",
            "payment_method": "cash",
            "status": "pending_confirmation",
        }
        data.update(overrides)
        return Order.objects.create(**data)

    def payload(self, *, event_id="message-1", phone="201012345678", action="confirm", from_me=False):
        reference = make_order_reference(self.order)
        return {
            "event": "messages.upsert",
            "data": {
                "key": {"id": event_id, "remoteJid": f"{phone}@s.whatsapp.net", "fromMe": from_me},
                "message": {"buttonsResponseMessage": {"selectedButtonId": f"{action}_order_{reference}"}},
            },
        }

    def post(self, payload, secret="test-webhook-secret"):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            headers={"X-Webhook-Secret": secret},
        )

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_confirmed_message")
    def test_confirm_changes_pending_order_once(self, mocked_message):
        response = self.post(self.payload())
        self.order.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.order.status, "confirmed")
        self.assertEqual(self.order.confirmation_method, "whatsapp")
        self.assertIsNotNone(self.order.confirmed_at)
        mocked_message.assert_called_once()

        duplicate = self.post(self.payload())
        self.assertEqual(duplicate.json()["status"], "duplicate")
        mocked_message.assert_called_once()
        self.assertEqual(WhatsAppWebhookEvent.objects.count(), 1)

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_cancelled_message")
    def test_cancel_changes_pending_order(self, mocked_message):
        response = self.post(self.payload(action="cancel"))
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "cancelled")
        self.assertEqual(self.order.status, "cancelled")
        mocked_message.assert_called_once()

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_edit_prompt")
    def test_edit_button_keeps_order_pending_and_requests_details(self, mocked_message):
        response = self.post(self.payload(action="edit", event_id="edit-1"))
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "edit_requested")
        self.assertEqual(self.order.status, "pending_confirmation")
        self.assertEqual(self.order.confirmation_method, "whatsapp_edit_requested")
        self.assertTrue(self.order.timeline.filter(note__contains="طلب العميل تعديل").exists())
        mocked_message.assert_called_once_with(self.order)

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_edit_received_message")
    def test_message_after_edit_button_is_saved_in_order_timeline(self, mocked_message):
        self.order.confirmation_method = "whatsapp_edit_requested"
        self.order.save(update_fields=["confirmation_method"])
        payload = self.payload(event_id="edit-details")
        payload["data"]["message"] = {"conversation": "تغيير العنوان إلى شارع النصر"}
        response = self.post(payload)
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "edit_received")
        self.assertEqual(self.order.confirmation_method, "whatsapp_edit_received")
        self.assertTrue(self.order.timeline.filter(note__contains="شارع النصر").exists())
        mocked_message.assert_called_once_with(self.order)

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_confirmed_message")
    def test_wrong_phone_cannot_confirm_order(self, mocked_message):
        response = self.post(self.payload(phone="201111111111"))
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "phone_mismatch")
        self.assertEqual(self.order.status, "pending_confirmation")
        mocked_message.assert_not_called()

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_confirmed_message")
    def test_lid_sender_uses_sender_phone_number(self, mocked_message):
        payload = self.payload(event_id="lid-confirm")
        payload["data"]["key"].update({
            "remoteJid": "123456789012345@lid",
            "senderPn": "201012345678@s.whatsapp.net",
        })
        response = self.post(payload)
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "confirmed")
        self.assertEqual(self.order.status, "confirmed")
        mocked_message.assert_called_once()

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_cancelled_message")
    def test_wrapped_button_response_is_processed(self, mocked_message):
        payload = self.payload(action="cancel", event_id="wrapped-cancel")
        button_message = payload["data"]["message"]
        payload["data"]["message"] = {"ephemeralMessage": {"message": button_message}}
        response = self.post(payload)
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "cancelled")
        self.assertEqual(self.order.status, "cancelled")
        mocked_message.assert_called_once()

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_edit_prompt")
    def test_button_display_text_fallback_is_processed(self, mocked_message):
        payload = self.payload(event_id="label-edit")
        payload["data"]["message"] = {
            "buttonsResponseMessage": {"selectedDisplayText": "✏️ تعديل الطلب"},
        }
        response = self.post(payload)
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "edit_requested")
        self.assertEqual(self.order.confirmation_method, "whatsapp_edit_requested")
        mocked_message.assert_called_once()

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_already_processed_message")
    def test_cancel_after_confirm_does_not_change_status(self, mocked_message):
        self.order.status = "confirmed"
        self.order.save(update_fields=["status"])
        response = self.post(self.payload(action="cancel", event_id="message-2"))
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "already_processed")
        self.assertEqual(self.order.status, "confirmed")
        mocked_message.assert_called_once()

    def test_invalid_webhook_secret_is_rejected(self):
        response = self.post(self.payload(), secret="wrong")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(WhatsAppWebhookEvent.objects.exists())

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_confirmed_message")
    def test_numeric_fallback_only_uses_one_pending_order_for_phone(self, mocked_message):
        payload = self.payload()
        payload["data"]["key"]["id"] = "fallback-1"
        payload["data"]["message"] = {"conversation": "1"}
        response = self.post(payload)
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "confirmed")
        self.assertEqual(self.order.status, "confirmed")
        mocked_message.assert_called_once()

    def test_numeric_fallback_refuses_ambiguous_pending_orders(self):
        self.create_order(customer_email="second@example.com")
        payload = self.payload(event_id="fallback-2")
        payload["data"]["message"] = {"conversation": "1"}
        response = self.post(payload)
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "ambiguous_or_missing")
        self.assertEqual(self.order.status, "pending_confirmation")

    def test_messages_sent_by_the_instance_are_ignored(self):
        response = self.post(self.payload(from_me=True))
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "ignored")
        self.assertEqual(self.order.status, "pending_confirmation")
