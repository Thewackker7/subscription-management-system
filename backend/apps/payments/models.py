from decimal import Decimal
from uuid import uuid4

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.billing.models import Invoice


def payment_identifier():
    return f"PAY-{uuid4().hex[:12].upper()}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank transfer"
        UPI = "UPI", "UPI"
        OTHER = "OTHER", "Other"

    identifier = models.CharField(max_length=20, unique=True, default=payment_identifier, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    method = models.CharField(max_length=20, choices=Method.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    payment_date = models.DateField(default=timezone.localdate, db_index=True)
    note = models.TextField(blank=True)
    external_reference = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["external_reference"], condition=Q(external_reference__isnull=False), name="unique_payment_external_reference")]
        indexes = [models.Index(fields=["invoice", "payment_date"])]
        ordering = ["-payment_date", "-created_at"]
