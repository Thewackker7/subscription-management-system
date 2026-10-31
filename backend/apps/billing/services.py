from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.subscriptions.models import Subscription, money
from .models import Invoice, InvoiceLine


def add_interval(start, interval, count):
    if interval == "DAILY":
        return start + timedelta(days=count)
    if interval == "WEEKLY":
        return start + timedelta(weeks=count)
    months = count if interval == "MONTHLY" else count * 12
    month_index = start.month - 1 + months
    year, month = start.year + month_index // 12, month_index % 12 + 1
    return date(year, month, min(start.day, monthrange(year, month)[1]))


def billing_period(subscription):
    period_start = subscription.next_billing_date or subscription.start_date
    next_start = add_interval(period_start, subscription.plan.billing_interval, subscription.plan.interval_count)
    return period_start, min(next_start - timedelta(days=1), subscription.expiry_date)


@transaction.atomic
def generate_invoice_for_subscription(subscription_id, as_of=None):
    as_of = as_of or timezone.localdate()
    subscription = Subscription.objects.select_for_update().select_related("customer", "plan").prefetch_related("lines__product", "lines__variant", "lines__tax_rule").get(pk=subscription_id)
    if subscription.status != Subscription.Status.ACTIVE or subscription.is_paused:
        return None, False
    period_start, period_end = billing_period(subscription)
    if period_start > subscription.expiry_date:
        subscription.transition(Subscription.Status.CLOSED)
        return None, False
    if period_start > as_of:
        return None, False
    existing = Invoice.objects.filter(subscription=subscription, billing_period_start=period_start, billing_period_end=period_end).first()
    if existing:
        return existing, False
    customer_name = f"{subscription.customer.first_name} {subscription.customer.last_name}".strip()
    invoice = Invoice(subscription=subscription, customer=subscription.customer, customer_email=subscription.customer.email,
                      customer_name=customer_name, billing_period_start=period_start, billing_period_end=period_end,
                      issue_date=as_of, due_date=as_of + timedelta(days=subscription.payment_terms_days))
    if not subscription.lines.all():
        raise ValueError("Cannot bill a subscription with no lines.")
    try:
        # A nested savepoint keeps the outer transaction usable after a unique race.
        with transaction.atomic():
            invoice.save()
    except IntegrityError:
        # Unique constraint makes concurrent retries idempotent even where locking semantics differ.
        return Invoice.objects.get(subscription=subscription, billing_period_start=period_start, billing_period_end=period_end), False
    subtotal = tax_total = Decimal("0.00")
    for source in subscription.lines.all():
        InvoiceLine.objects.create(invoice=invoice, product=source.product, variant=source.variant, description=source.description,
                                   quantity=source.quantity, unit_price=source.unit_price, tax_rule=source.tax_rule,
                                   tax_rate=source.tax_rate, subtotal=source.subtotal, tax_amount=source.tax_amount, total=source.total)
        subtotal += source.subtotal
        tax_total += source.tax_amount
    invoice.subtotal, invoice.tax_total, invoice.total = money(subtotal), money(tax_total), money(subtotal + tax_total)
    invoice.save(update_fields=["subtotal", "tax_total", "total"])
    # Import here to avoid a billing/discount model import cycle during Django startup.
    from apps.discounts.services import apply_eligible_discounts
    invoice = apply_eligible_discounts(invoice.id, as_of)
    subscription.next_billing_date = period_end + timedelta(days=1)
    subscription.save(update_fields=["next_billing_date", "updated_at"])
    if period_end >= subscription.expiry_date:
        subscription.transition(Subscription.Status.CLOSED)
    return invoice, True


def generate_due_invoices(as_of=None):
    as_of = as_of or timezone.localdate()
    subscription_ids = list(Subscription.objects.filter(status=Subscription.Status.ACTIVE, is_paused=False, next_billing_date__lte=as_of).values_list("id", flat=True))
    generated, existing = [], []
    for subscription_id in subscription_ids:
        invoice, created = generate_invoice_for_subscription(subscription_id, as_of)
        if invoice:
            (generated if created else existing).append(invoice)
    return generated, existing
