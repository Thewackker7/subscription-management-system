from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Product(models.Model):
    class ProductType(models.TextChoices):
        SERVICE = "SERVICE", "Service"
        GOODS = "GOODS", "Goods"
        DIGITAL = "DIGITAL", "Digital"

    name = models.CharField(max_length=200, unique=True)
    product_type = models.CharField(max_length=20, choices=ProductType.choices)
    sales_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="variants")
    label = models.CharField(max_length=150)
    extra_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    sku = models.CharField(max_length=80, blank=True, unique=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["product", "label"], name="unique_variant_label_per_product")]
        ordering = ["product__name", "label"]

    @property
    def sales_price(self):
        return self.product.sales_price + self.extra_price

    def __str__(self):
        return f"{self.product.name} - {self.label}"


class Plan(models.Model):
    class BillingInterval(models.TextChoices):
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        MONTHLY = "MONTHLY", "Monthly"
        YEARLY = "YEARLY", "Yearly"

    name = models.CharField(max_length=150, unique=True)
    billing_interval = models.CharField(max_length=10, choices=BillingInterval.choices)
    interval_count = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    minimum_quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    available_from = models.DateField(null=True, blank=True)
    available_until = models.DateField(null=True, blank=True)
    allow_pause = models.BooleanField(default=False)
    allow_renewal = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(available_until__isnull=True) | Q(available_from__isnull=True) | Q(available_until__gte=models.F("available_from")), name="plan_availability_dates_valid")]
        ordering = ["name"]

    def __str__(self):
        return self.name


class TaxRule(models.Model):
    name = models.CharField(max_length=100, unique=True)
    rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    is_active = models.BooleanField(default=True)
    available_from = models.DateField(null=True, blank=True)
    available_until = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(rate__lte=Decimal("100.00")), name="tax_rate_not_above_100"),
            models.CheckConstraint(condition=Q(available_until__isnull=True) | Q(available_from__isnull=True) | Q(available_until__gte=models.F("available_from")), name="tax_availability_dates_valid"),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.rate}%)"
