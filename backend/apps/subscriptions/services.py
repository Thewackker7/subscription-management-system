from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Quotation, Subscription, SubscriptionLine


@transaction.atomic
def convert_quotation_to_subscription(*, quotation_id, start_date, expiry_date, payment_terms_days=30):
    quotation = Quotation.objects.select_for_update().select_related("customer", "plan").prefetch_related("lines__product", "lines__variant", "lines__tax_rule").get(pk=quotation_id)
    if quotation.converted_subscription_id or quotation.status == Quotation.Status.CONVERTED:
        raise ValidationError({"detail": "Quotation has already been converted."})
    if quotation.status not in {Quotation.Status.DRAFT, Quotation.Status.SENT, Quotation.Status.ACCEPTED}:
        raise ValidationError({"detail": "Quotation is not eligible for conversion."})
    if quotation.valid_until < timezone.localdate():
        quotation.status = Quotation.Status.EXPIRED
        quotation.save(update_fields=["status"])
        raise ValidationError({"detail": "Quotation has expired."})
    if not quotation.lines.exists():
        raise ValidationError({"detail": "Quotation requires at least one line."})
    subscription = Subscription(customer=quotation.customer, plan=quotation.plan, start_date=start_date,
                                expiry_date=expiry_date, payment_terms_days=payment_terms_days,
                                status=Subscription.Status.CONFIRMED)
    subscription.full_clean()
    subscription.save()
    for line in quotation.lines.all():
        subscription_line = SubscriptionLine(subscription=subscription, product=line.product, variant=line.variant,
                                             description=line.description, quantity=line.quantity, unit_price=line.unit_price,
                                             tax_rule=line.tax_rule, tax_rate=line.tax_rate)
        subscription_line.full_clean()
        subscription_line.save()
    quotation.converted_subscription = subscription
    quotation.status = Quotation.Status.CONVERTED
    quotation.save(update_fields=["converted_subscription", "status"])
    return subscription
