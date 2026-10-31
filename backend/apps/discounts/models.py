from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.catalog.models import Product
from apps.billing.models import Invoice


class DiscountRule(models.Model):
    class DiscountType(models.TextChoices):
        FIXED = "FIXED", "Fixed amount"
        PERCENTAGE = "PERCENTAGE", "Percentage"

    class Scope(models.TextChoices):
        SUBSCRIPTION = "SUBSCRIPTION", "Subscription-wide"
        PRODUCT = "PRODUCT", "Product-specific"

    name = models.CharField(max_length=150, unique=True)
    discount_type = models.CharField(max_length=12, choices=DiscountType.choices)
    value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    scope = models.CharField(max_length=16, choices=Scope.choices, default=Scope.SUBSCRIPTION)
    products = models.ManyToManyField(Product, blank=True, related_name="discount_rules")
    minimum_purchase_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    minimum_quantity = models.PositiveIntegerField(default=0)
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True)
    maximum_uses = models.PositiveIntegerField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(ends_on__isnull=True) | Q(ends_on__gte=models.F("starts_on")), name="discount_dates_valid"),
            models.CheckConstraint(condition=Q(discount_type="FIXED") | Q(value__lte=Decimal("100.00")), name="discount_percentage_not_above_100"),
        ]
        indexes = [models.Index(fields=["is_active", "starts_on", "ends_on"])]
        ordering = ["id"]


class DiscountApplication(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="discount_applications")
    rule = models.ForeignKey(DiscountRule, on_delete=models.PROTECT, related_name="applications")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["invoice", "rule"], name="unique_discount_rule_per_invoice")]
        indexes = [models.Index(fields=["rule", "applied_at"])]
