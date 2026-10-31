from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.billing.services import generate_due_invoices


class Command(BaseCommand):
    help = "Generate idempotent invoices for active subscriptions due on or before a date."

    def add_arguments(self, parser):
        parser.add_argument("--as-of", help="Billing cutoff date in YYYY-MM-DD format.")

    def handle(self, *args, **options):
        as_of = None
        if options["as_of"]:
            try:
                as_of = date.fromisoformat(options["as_of"])
            except ValueError as exc:
                raise CommandError("--as-of must be YYYY-MM-DD") from exc
        generated, existing = generate_due_invoices(as_of)
        self.stdout.write(self.style.SUCCESS(f"Generated {len(generated)} invoice(s); {len(existing)} existing invoice(s) returned."))
