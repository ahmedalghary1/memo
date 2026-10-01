import json
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.orders.models import Order, OrderItem, WhatsAppWebhookEvent
from apps.orders.whatsapp.services import (
    EvolutionAPIClient,
    EvolutionAPIError,
    make_order_edit_token,
    make_order_reference,
    normalize_phone_number,
)


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
    def test_order_confirmation_always_uses_reliable_numeric_text(self):
        client = EvolutionAPIClient()
        with patch.object(client, "send_text", return_value={"key": {"id": "outbound-123", "remoteJid": "123456789@lid"}}) as mocked_text, patch.object(client, "send_buttons") as mocked_buttons:
            self.assertTrue(client.send_order_confirmation(self.order))
        self.order.refresh_from_db()
        self.assertIsNotNone(self.order.whatsapp_confirmation_sent_at)
        self.assertEqual(self.order.whatsapp_message_id, "outbound-123")
        self.assertEqual(self.order.whatsapp_chat_jid, "123456789@lid")
        mocked_buttons.assert_not_called()
        message = mocked_text.call_args.args[1]
        self.assertIn("أدخل رقم 1 للتأكيد", message)
        self.assertIn("أدخل رقم 2 للتعديل", message)
        self.assertIn("أدخل رقم 3 للإلغاء", message)
        self.assertIn(f"1 {self.order.order_number}", message)

    def test_order_confirmation_failure_does_not_mark_message_sent(self):
        client = EvolutionAPIClient()
        with patch.object(client, "send_text", side_effect=EvolutionAPIError("unavailable")):
            self.assertFalse(client.send_order_confirmation(self.order))
        self.order.refresh_from_db()
        self.assertIsNone(self.order.whatsapp_confirmation_sent_at)

    @override_settings(EVOLUTION_USE_BUTTONS=False)
    def test_order_confirmation_uses_reliable_text_mode_by_default(self):
        client = EvolutionAPIClient()
        with patch.object(client, "send_text", return_value={}) as mocked_text, patch.object(client, "send_buttons") as mocked_buttons:
            self.assertTrue(client.send_order_confirmation(self.order))
        mocked_buttons.assert_not_called()
        self.assertIn(f"1 {self.order.order_number}", mocked_text.call_args.args[1])

    @override_settings(PUBLIC_ORIGIN="https://store.example")
    def test_edit_reply_contains_signed_website_link(self):
        client = EvolutionAPIClient()
        with patch.object(client, "send_text", return_value={}) as mocked_text:
            client.send_order_edit_prompt(self.order)
        message = mocked_text.call_args.args[1]
        self.assertIn("https://store.example/orders/edit/", message)
        self.assertIn("رابط", message)

    def test_text_message_accepts_lid_recipient(self):
        client = EvolutionAPIClient()
        with patch.object(client, "_post", return_value={}) as mocked_post:
            client.send_text("123456789@lid", "test")
        mocked_post.assert_called_once_with(
            "message/sendText", {"number": "123456789@lid", "text": "test"},
        )

    def test_acknowledgement_uses_saved_lid_chat(self):
        self.order.whatsapp_chat_jid = "123456789@lid"
        client = EvolutionAPIClient()
        with patch.object(client, "send_text", return_value={}) as mocked_text:
            client.send_order_confirmed_message(self.order)
        self.assertEqual(mocked_text.call_args.args[0], "123456789@lid")
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

    def post_with_query_token(self, payload, token="test-webhook-secret"):
        return self.client.post(
            f"{self.url}?token={token}",
            data=json.dumps(payload),
            content_type="application/json",
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
        event = WhatsAppWebhookEvent.objects.get()
        self.assertEqual(event.order, self.order)
        self.assertEqual(event.outcome, "confirmed")
        self.assertIsNotNone(event.acknowledged_at)
        self.assertEqual(event.acknowledgement_attempts, 1)

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_confirmed_message")
    def test_failed_acknowledgement_is_retried_without_reprocessing_order(self, mocked_message):
        mocked_message.side_effect = [EvolutionAPIError("temporary"), {}]
        payload = self.payload(event_id="ack-retry")

        first = self.post(payload)
        self.order.refresh_from_db()
        self.assertEqual(first.status_code, 503)
        self.assertEqual(first.json()["acknowledgement"], "retry")
        self.assertEqual(self.order.status, "confirmed")
        event = WhatsAppWebhookEvent.objects.get(event_id="ack-retry")
        self.assertIsNone(event.acknowledged_at)
        self.assertEqual(event.acknowledgement_attempts, 1)

        second = self.post(payload)
        event.refresh_from_db()
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["status"], "confirmed")
        self.assertIsNotNone(event.acknowledged_at)
        self.assertEqual(event.acknowledgement_attempts, 2)
        self.assertEqual(self.order.timeline.filter(status="confirmed").count(), 1)
        self.assertEqual(mocked_message.call_count, 2)

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
        self.assertEqual(self.order.whatsapp_chat_jid, "123456789012345@lid")
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

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_edit_prompt")
    def test_number_two_requests_edit(self, mocked_message):
        payload = self.payload(event_id="numeric-edit")
        payload["data"]["message"] = {"conversation": "2"}
        response = self.post(payload)
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "edit_requested")
        self.assertEqual(self.order.confirmation_method, "whatsapp_edit_requested")
        mocked_message.assert_called_once()

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_cancelled_message")
    def test_number_three_cancels_order(self, mocked_message):
        payload = self.payload(event_id="numeric-cancel")
        payload["data"]["message"] = {"conversation": "3"}
        response = self.post(payload)
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "cancelled")
        self.assertEqual(self.order.status, "cancelled")
        mocked_message.assert_called_once()

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_confirmed_message")
    def test_lid_only_existing_chat_is_matched_and_confirmed(self, mocked_message):
        self.order.whatsapp_chat_jid = "123456789@lid"
        self.order.save(update_fields=["whatsapp_chat_jid"])
        payload = self.payload(event_id="lid-only-existing")
        payload["data"]["key"]["remoteJid"] = "123456789@lid"
        payload["data"]["message"] = {"conversation": "1"}
        response = self.post(payload)
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "confirmed")
        self.assertEqual(self.order.status, "confirmed")
        mocked_message.assert_called_once()
    def test_invalid_webhook_secret_is_rejected(self):
        response = self.post(self.payload(), secret="wrong")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(WhatsAppWebhookEvent.objects.exists())

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_confirmed_message")
    def test_global_webhook_query_token_is_accepted(self, mocked_message):
        response = self.post_with_query_token(self.payload(event_id="global-hook"))
        self.order.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.order.status, "confirmed")
        mocked_message.assert_called_once()

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

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_confirmed_message")
    def test_bare_number_selects_newest_pending_order_for_same_phone(self, mocked_message):
        newest = self.create_order(customer_email="second@example.com")
        payload = self.payload(event_id="fallback-2")
        payload["data"]["message"] = {"conversation": "1"}
        response = self.post(payload)
        self.order.refresh_from_db()
        newest.refresh_from_db()
        self.assertEqual(response.json()["status"], "confirmed")
        self.assertEqual(self.order.status, "pending_confirmation")
        self.assertEqual(newest.status, "confirmed")
        mocked_message.assert_called_once_with(newest)

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_confirmed_message")
    def test_numeric_reply_with_order_number_selects_correct_order(self, mocked_message):
        other = self.create_order(customer_email="second@example.com")
        payload = self.payload(event_id="numbered-reply")
        payload["data"]["message"] = {"conversation": f"1 {self.order.order_number.lower()}"}
        response = self.post(payload)
        self.order.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(response.json()["status"], "confirmed")
        self.assertEqual(self.order.status, "confirmed")
        self.assertEqual(other.status, "pending_confirmation")
        mocked_message.assert_called_once()

    @patch("apps.orders.whatsapp.views.EvolutionAPIClient.send_order_confirmed_message")
    def test_reply_to_confirmation_message_selects_that_order(self, mocked_message):
        self.order.whatsapp_message_id = "older-outbound-id"
        self.order.save(update_fields=["whatsapp_message_id"])
        newest = self.create_order(customer_email="newest@example.com")
        newest.whatsapp_message_id = "newer-outbound-id"
        newest.save(update_fields=["whatsapp_message_id"])
        payload = self.payload(event_id="quoted-reply")
        payload["data"]["message"] = {
            "extendedTextMessage": {
                "text": "1",
                "contextInfo": {"stanzaId": "older-outbound-id"},
            }
        }
        response = self.post(payload)
        self.order.refresh_from_db()
        newest.refresh_from_db()
        self.assertEqual(response.json()["status"], "confirmed")
        self.assertEqual(self.order.status, "confirmed")
        self.assertEqual(newest.status, "pending_confirmation")
        mocked_message.assert_called_once_with(self.order)

    def test_messages_sent_by_the_instance_are_ignored(self):
        response = self.post(self.payload(from_me=True))
        self.order.refresh_from_db()
        self.assertEqual(response.json()["status"], "ignored")
        self.assertEqual(self.order.status, "pending_confirmation")


class WhatsAppOrderEditTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            status="pending_confirmation",
            subtotal=500,
            shipping_total=70,
            grand_total=570,
            customer_name="Customer",
            customer_phone="01012345678",
            customer_email="customer@example.com",
            governorate="القاهرة",
            area="مدينة نصر",
            address_line="شارع أول",
            payment_method="cash",
        )
        OrderItem.objects.create(
            order=self.order,
            product_name="T-Shirt",
            variant_sku="TEE-B-M",
            size_name="M",
            color_name="Black",
            unit_price=500,
            quantity=1,
            line_total=500,
        )
        self.token = make_order_edit_token(self.order)
        self.url = reverse("orders:whatsapp_edit", kwargs={"token": self.token})

    def test_signed_link_displays_order_edit_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.order.order_number)
        self.assertContains(response, "تعديل بيانات الطلب")

    def test_customer_can_update_delivery_details(self):
        response = self.client.post(self.url, {
            "customer_name": "عميل جديد",
            "customer_phone": "01012345678",
            "customer_email": "new@example.com",
            "governorate": "القاهرة",
            "area": "المعادي",
            "address_line": "شارع النصر",
            "address_details": "الدور الثاني",
            "notes": "الاتصال قبل الوصول",
        }, follow=True)
        self.order.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.order.area, "المعادي")
        self.assertEqual(self.order.address_line, "شارع النصر")
        self.assertEqual(self.order.confirmation_method, "whatsapp_edit_received")
        self.assertTrue(self.order.timeline.filter(note__contains="رابط WhatsApp").exists())
        self.assertContains(response, "تم حفظ التعديلات")

    def test_invalid_edit_token_is_rejected(self):
        response = self.client.get(reverse("orders:whatsapp_edit", kwargs={"token": "invalid"}))
        self.assertEqual(response.status_code, 404)

    def test_confirmed_order_cannot_be_edited(self):
        self.order.status = "confirmed"
        self.order.save(update_fields=["status"])
        response = self.client.post(self.url, {
            "customer_name": "Changed Name",
            "customer_phone": "01012345678",
            "customer_email": "new@example.com",
            "governorate": "القاهرة",
            "area": "المعادي",
            "address_line": "شارع النصر",
            "address_details": "",
            "notes": "",
        })
        self.order.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.order.customer_name, "Customer")
        self.assertContains(response, "لا يمكن تعديل هذا الطلب الآن")
