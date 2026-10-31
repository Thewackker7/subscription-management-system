from decimal import Decimal

from django.db import transaction
from django.db.models import F, Q

from apps.billing.models import Invoice
from apps.subscriptions.models import money
from .models import DiscountApplication, DiscountRule


def _eligible_lines(rule, invoice):
    lines = list(invoice.lines.select_related("product").all())
    if rule.scope == DiscountRule.Scope.SUBSCRIPTION:
        return lines
    product_ids = set(rule.products.values_list("id", flat=True))
    return [line for line in lines if line.product_id in product_ids]


@transaction.atomic
def apply_eligible_discounts(invoice_id, as_of):
    """Apply each eligible rule once; caller may safely retry due to locks + constraints."""
    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
    rules = DiscountRule.objects.select_for_update().filter(is_active=True, starts_on__lte=as_of).filter(
        Q(ends_on__isnull=True) | Q(ends_on__gte=as_of)
    ).prefetch_related("products")
    total_discount = Decimal("0.00")
    line_discounts = {}
    for rule in rules:
        if rule.maximum_uses is not None and rule.usage_count >= rule.maximum_uses:
            continue
        lines = _eligible_lines(rule, invoice)
        eligible_subtotal = sum((line.subtotal for line in lines), Decimal("0.00"))
        eligible_quantity = sum((line.quantity for line in lines), 0)
        if not lines or eligible_subtotal < rule.minimum_purchase_amount or eligible_quantity < rule.minimum_quantity:
            continue
        already_allocated = sum((line_discounts.get(line.id, Decimal("0.00")) for line in lines), Decimal("0.00"))
        remaining = max(Decimal("0.00"), eligible_subtotal - already_allocated)
        amount = money(rule.value if rule.discount_type == DiscountRule.DiscountType.FIXED else eligible_subtotal * rule.value / Decimal("100"))
        amount = min(amount, remaining)
        if amount <= 0:
            continue
        DiscountApplication.objects.create(invoice=invoice, rule=rule, amount=amount)
        DiscountRule.objects.filter(pk=rule.pk).update(usage_count=F("usage_count") + 1)
        total_discount += amount
        # Proportionally allocate the rule to applicable invoice lines for tax-after-discount.
        remaining_amount = amount
        for index, line in enumerate(lines):
            allocated = remaining_amount if index == len(lines) - 1 else money(amount * line.subtotal / eligible_subtotal)
            line_discounts[line.id] = line_discounts.get(line.id, Decimal("0.00")) + allocated
            remaining_amount -= allocated
    tax_total = Decimal("0.00")
    for line in invoice.lines.all():
        taxable = max(Decimal("0.00"), line.subtotal - line_discounts.get(line.id, Decimal("0.00")))
        line.tax_amount = money(taxable * line.tax_rate / Decimal("100"))
        line.total = taxable + line.tax_amount
        line.save(update_fields=["tax_amount", "total"])
        tax_total += line.tax_amount
    invoice.discount_total = money(total_discount)
    invoice.tax_total = money(tax_total)
    invoice.total = money(invoice.subtotal - invoice.discount_total + invoice.tax_total)
    invoice.save(update_fields=["discount_total", "tax_total", "total"])
    return invoice
