from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Product, ProductVariant, TaxRule
from apps.subscriptions.models import Subscription, money


def invoice_number():
    return f"INV-{uuid4().hex[:12].upper()}"


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"

    number = models.CharField(max_length=20, unique=True, default=invoice_number, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT, related_name="invoices")
    customer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="invoices")
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=301, blank=True)
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(db_index=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    sent_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["subscription", "billing_period_start", "billing_period_end"], name="unique_subscription_billing_period"),
            models.CheckConstraint(condition=Q(billing_period_end__gte=models.F("billing_period_start")), name="invoice_period_valid"),
        ]
        indexes = [models.Index(fields=["customer", "status"]), models.Index(fields=["status", "due_date"]), models.Index(fields=["subscription", "billing_period_start"])]
        ordering = ["-issue_date", "-created_at"]

    @property
    def balance(self):
        return max(Decimal("0.00"), self.total - self.amount_paid)

    @property
    def is_overdue(self):
        return self.status == self.Status.CONFIRMED and self.due_date < timezone.localdate() and self.balance > 0

    def confirm(self):
        if self.status != self.Status.DRAFT:
            raise ValidationError({"detail": "Only draft invoices can be confirmed."})
        self.status = self.Status.CONFIRMED
        self.save(update_fields=["status"])

    def cancel(self):
        if self.status not in {self.Status.DRAFT, self.Status.CONFIRMED} or self.amount_paid > 0:
            raise ValidationError({"detail": "Invoices with payments or final status cannot be cancelled."})
        self.status = self.Status.CANCELLED
        self.cancelled_at = timezone.now()
        self.save(update_fields=["status", "cancelled_at"])


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rule = models.ForeignKey(TaxRule, on_delete=models.PROTECT, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2)
    total = models.DecimalField(max_digits=14, decimal_places=2)

    def clean(self):
        if self.variant_id and self.product_id and self.variant.product_id != self.product_id:
            raise ValidationError({"variant": "Variant must belong to product."})
