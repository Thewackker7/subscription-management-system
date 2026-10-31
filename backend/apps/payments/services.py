from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from apps.billing.models import Invoice
from apps.subscriptions.models import money
from .models import Payment


@transaction.atomic
def record_payment(*, invoice_id, method, amount, payment_date, note="", external_reference=None):
    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
    amount = money(amount)
    if invoice.status not in {Invoice.Status.CONFIRMED, Invoice.Status.PAID}:
        raise ValidationError({"invoice": "Only confirmed invoices can receive payments."})
    if amount <= 0:
        raise ValidationError({"amount": "Payment amount must be positive."})
    if amount > invoice.balance:
        raise ValidationError({"amount": "Payment exceeds the outstanding balance."})
    if external_reference == "":
        external_reference = None
    try:
        with transaction.atomic():
            payment = Payment.objects.create(invoice=invoice, method=method, amount=amount, payment_date=payment_date,
                                             note=note, external_reference=external_reference)
    except IntegrityError as exc:
        raise ValidationError({"external_reference": "This external reference has already been recorded."}) from exc
    invoice.amount_paid = money(invoice.amount_paid + amount)
    if invoice.amount_paid == invoice.total:
        invoice.status = Invoice.Status.PAID
    invoice.save(update_fields=["amount_paid", "status"])
    return payment
