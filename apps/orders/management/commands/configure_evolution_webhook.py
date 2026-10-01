from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.orders.whatsapp.services import EvolutionAPIClient, EvolutionAPIError


class Command(BaseCommand):
    help = "Configure the Evolution API instance webhook used for order confirmations."

    def handle(self, *args, **options):
        missing = [
            name
            for name in (
                "EVOLUTION_API_URL",
                "EVOLUTION_API_KEY",
                "EVOLUTION_INSTANCE",
                "EVOLUTION_WEBHOOK_URL",
                "EVOLUTION_WEBHOOK_SECRET",
            )
            if not getattr(settings, name, "")
        ]
        if missing:
            raise CommandError(f"Missing Evolution settings: {', '.join(missing)}")
        if len(settings.EVOLUTION_WEBHOOK_SECRET) < 32:
            raise CommandError("EVOLUTION_WEBHOOK_SECRET must contain at least 32 characters.")
        try:
            client = EvolutionAPIClient()
            created = client.ensure_instance() if settings.EVOLUTION_CREATE_INSTANCE else False
            client.configure_webhook(
                settings.EVOLUTION_WEBHOOK_URL,
                settings.EVOLUTION_WEBHOOK_SECRET,
            )
        except EvolutionAPIError as exc:
            raise CommandError(str(exc)) from exc
        if created:
            self.stdout.write(self.style.SUCCESS(f"Evolution instance '{settings.EVOLUTION_INSTANCE}' created."))
        self.stdout.write(self.style.SUCCESS("Evolution webhook configured successfully."))
