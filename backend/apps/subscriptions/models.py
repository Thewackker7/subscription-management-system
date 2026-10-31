from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Plan, Product, ProductVariant, TaxRule

CENT = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def subscription_number():
    return f"SUB-{uuid4().hex[:12].upper()}"


def quotation_number():
    return f"QTE-{uuid4().hex[:12].upper()}"


class Subscription(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        QUOTATION = "QUOTATION", "Quotation"
        CONFIRMED = "CONFIRMED", "Confirmed"
        ACTIVE = "ACTIVE", "Active"
        CLOSED = "CLOSED", "Closed"

    number = models.CharField(max_length=20, unique=True, default=subscription_number, editable=False)
    customer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="subscriptions", limit_choices_to={"role": User.Role.CUSTOMER})
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    start_date = models.DateField()
    expiry_date = models.DateField()
    payment_terms_days = models.PositiveSmallIntegerField(default=30)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)
    next_billing_date = models.DateField(null=True, blank=True, db_index=True)
    is_paused = models.BooleanField(default=False)
    paused_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["customer", "status"]), models.Index(fields=["status", "next_billing_date"])]
        constraints = [models.CheckConstraint(condition=Q(expiry_date__gte=models.F("start_date")), name="subscription_expiry_after_start")]
        ordering = ["-created_at"]

    def clean(self):
        if self.customer_id and self.customer.role != User.Role.CUSTOMER:
            raise ValidationError({"customer": "Subscriptions can only belong to Customer users."})
        if self.plan_id:
            if not self.plan.is_active:
                raise ValidationError({"plan": "Plan is inactive."})
            if self.plan.available_from and self.start_date < self.plan.available_from:
                raise ValidationError({"start_date": "Plan is not available yet."})
            if self.plan.available_until and self.start_date > self.plan.available_until:
                raise ValidationError({"start_date": "Plan is no longer available."})

    def transition(self, target):
        allowed = {
            self.Status.DRAFT: {self.Status.QUOTATION, self.Status.CLOSED},
            self.Status.QUOTATION: {self.Status.CONFIRMED, self.Status.CLOSED},
            self.Status.CONFIRMED: {self.Status.ACTIVE, self.Status.CLOSED},
            self.Status.ACTIVE: {self.Status.CLOSED},
            self.Status.CLOSED: set(),
        }
        if target not in allowed[self.status]:
            raise ValidationError({"status": f"Cannot transition from {self.status} to {target}."})
        self.status = target
        if target == self.Status.ACTIVE and not self.next_billing_date:
            self.next_billing_date = self.start_date
        if target == self.Status.CLOSED:
            self.closed_at = timezone.now()
            self.is_paused = False
        self.save(update_fields=["status", "next_billing_date", "closed_at", "is_paused", "updated_at"])

    def pause(self):
        if self.status != self.Status.ACTIVE or not self.plan.allow_pause:
            raise ValidationError({"detail": "This active subscription cannot be paused."})
        self.is_paused = True
        self.paused_at = timezone.now()
        self.save(update_fields=["is_paused", "paused_at", "updated_at"])

    def resume(self):
        if self.status != self.Status.ACTIVE or not self.is_paused:
            raise ValidationError({"detail": "Only paused active subscriptions can resume."})
        self.is_paused = False
        self.paused_at = None
        self.save(update_fields=["is_paused", "paused_at", "updated_at"])

    def renew(self, expiry_date):
        if not self.plan.allow_renewal or self.status != self.Status.CLOSED or expiry_date <= self.expiry_date:
            raise ValidationError({"detail": "This subscription cannot be renewed with the requested expiry date."})
        self.expiry_date = expiry_date
        self.status = self.Status.ACTIVE
        self.closed_at = None
        self.next_billing_date = self.next_billing_date or self.expiry_date
        self.save(update_fields=["expiry_date", "status", "closed_at", "next_billing_date", "updated_at"])


class SubscriptionLine(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rule = models.ForeignKey(TaxRule, on_delete=models.PROTECT, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(quantity__gte=1), name="subscription_line_quantity_positive")]

    def clean(self):
        if self.variant_id and self.variant.product_id != self.product_id:
            raise ValidationError({"variant": "Variant must belong to the selected product."})
        if self.quantity and self.subscription_id and self.quantity < self.subscription.plan.minimum_quantity:
            raise ValidationError({"quantity": "Quantity is below this plan's minimum quantity."})

    def calculate_totals(self):
        self.subtotal = money(self.quantity * self.unit_price)
        self.tax_amount = money(self.subtotal * self.tax_rate / Decimal("100"))
        self.total = self.subtotal + self.tax_amount

    def save(self, *args, **kwargs):
        self.calculate_totals()
        super().save(*args, **kwargs)


class QuotationTemplate(models.Model):
    name = models.CharField(max_length=150, unique=True)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="quotation_templates")
    validity_days = models.PositiveSmallIntegerField(default=30, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]


class QuotationTemplateLine(models.Model):
    template = models.ForeignKey(QuotationTemplate, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    tax_rule = models.ForeignKey(TaxRule, on_delete=models.PROTECT, null=True, blank=True)

    def clean(self):
        if self.variant_id and self.variant.product_id != self.product_id:
            raise ValidationError({"variant": "Variant must belong to the selected product."})


class Quotation(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent"
        ACCEPTED = "ACCEPTED", "Accepted"
        EXPIRED = "EXPIRED", "Expired"
        CONVERTED = "CONVERTED", "Converted"

    number = models.CharField(max_length=20, unique=True, default=quotation_number, editable=False)
    customer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="quotations", limit_choices_to={"role": User.Role.CUSTOMER})
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="quotations")
    valid_until = models.DateField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)
    notes = models.TextField(blank=True)
    converted_subscription = models.OneToOneField(Subscription, on_delete=models.PROTECT, null=True, blank=True, related_name="source_quotation")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["customer", "status"]), models.Index(fields=["status", "valid_until"])]
        ordering = ["-created_at"]


class QuotationLine(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rule = models.ForeignKey(TaxRule, on_delete=models.PROTECT, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    def save(self, *args, **kwargs):
        self.subtotal = money(self.quantity * self.unit_price)
        self.tax_amount = money(self.subtotal * self.tax_rate / Decimal("100"))
        self.total = self.subtotal + self.tax_amount
        super().save(*args, **kwargs)
